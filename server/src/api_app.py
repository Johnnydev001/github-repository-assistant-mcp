"""ASGI FastAPI application that creates a long-lived MCP client session on startup."""
from fastapi import FastAPI
from api.v1.api import router
from pathlib import Path
import asyncio
import os
import sys

from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp import ClientSession

app = FastAPI(title="Portfolio MCP Server API")
app.include_router(router, prefix="/api", tags=["API v1"], deprecated=False)


async def _mcp_runner(params: StdioServerParameters):
    """Background task that manages a long-lived stdio client + ClientSession.
    On startup it initializes and stores the session at app.state.mcp_session.
    The task runs until cancelled on shutdown.
    """
    try:
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                app.state.mcp_session = session
                # Wait indefinitely until cancelled
                await asyncio.Event().wait()
    except asyncio.CancelledError:
        # Shutdown requested; let contexts exit to cleanup
        return
    except Exception:
        # Store any startup failure for diagnostics
        app.state.mcp_session = None
        return


@app.on_event("startup")
async def startup_event():
    # Path to the server.py that implements the MCP tools
    server_py = Path(__file__).resolve().parent / "server.py"
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_py)],
        cwd=str(Path(__file__).resolve().parents[2]),
        env=os.environ.copy(),
    )
    # Launch background task
    app.state._mcp_task = asyncio.create_task(_mcp_runner(params))


@app.on_event("shutdown")
async def shutdown_event():
    task = getattr(app.state, "_mcp_task", None)
    if task:
        task.cancel()
        try:
            await task
        except Exception:
            pass
