"""ASGI FastAPI application that creates a long-lived MCP client session on startup."""
from fastapi import FastAPI
from api.v1.api import router
from pathlib import Path
import asyncio
import logging
import os
import sys

from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp import ClientSession

# Import config + github client so we can expose list_branches without going through MCP stdio
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import Settings
from github_client import GitHubRepositoryClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MCP Server API")
app.include_router(router, prefix="/api", tags=["API v1"], deprecated=False)

# Event set once the MCP session is ready (or failed)
_mcp_ready = asyncio.Event()


async def _mcp_runner(params: StdioServerParameters):
    """Background task that manages a long-lived stdio client + ClientSession."""
    try:
        logger.info("Starting MCP subprocess: %s %s", params.command, params.args)
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                app.state.mcp_session = session
                logger.info("MCP session initialized successfully")
                _mcp_ready.set()
                await asyncio.Event().wait()
    except asyncio.CancelledError:
        return
    except Exception as exc:
        logger.exception("MCP session failed to start: %s", exc)
        app.state.mcp_session = None
        _mcp_ready.set()  # unblock waiters even on failure


@app.on_event("startup")
async def startup_event():
    global _mcp_ready
    _mcp_ready = asyncio.Event()
    app.state.mcp_session = None

    server_py = Path(__file__).resolve().parent / "server.py"
    env = os.environ.copy()
    # Ensure PYTHONPATH includes server/src so server.py can import config etc.
    src_dir = str(Path(__file__).resolve().parent)
    env["PYTHONPATH"] = src_dir + os.pathsep + env.get("PYTHONPATH", "")

    params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_py)],
        cwd=str(Path(__file__).resolve().parents[2]),
        env=env,
    )

    app.state._mcp_task = asyncio.create_task(_mcp_runner(params))

    # Also expose a GitHubRepositoryClient directly for lightweight REST calls (e.g. list_branches)
    try:
        settings = Settings.load()
        app.state.github_client = GitHubRepositoryClient(
            owner=settings.repo_owner,
            repo=settings.repo_name,
            token=settings.github_token,
            ref=settings.repo_ref,
        )
        logger.info("GitHub client initialized for owner=%s repo=%s", settings.repo_owner, settings.repo_name)
    except Exception as exc:
        logger.warning("Could not initialize GitHub client: %s", exc)
        app.state.github_client = None

    # Wait up to 10 s for the session to be ready before accepting requests
    try:
        await asyncio.wait_for(_mcp_ready.wait(), timeout=10.0)
    except asyncio.TimeoutError:
        logger.warning("MCP session did not initialize within 10 s; continuing anyway")

    if app.state.mcp_session is None:
        logger.error("MCP session is NOT available. Check server.py logs above.")
    else:
        logger.info("API ready with MCP session")


@app.on_event("shutdown")
async def shutdown_event():
    task = getattr(app.state, "_mcp_task", None)
    if task:
        task.cancel()
        try:
            await task
        except Exception:
            pass
