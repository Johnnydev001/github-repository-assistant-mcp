from fastapi import APIRouter, HTTPException, Request
from pathlib import Path
import subprocess
import json
import anyio

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[3]

@router.get("/list-tools")
async def list_tools():
    return {"output": "test"}

@router.get("/read-file")
async def read_file(path: str):
    return {"output": "test"}


@router.get("/file-history")
async def get_file_history(file_name: str, branch: str = "main"):
    return {"output": "test"}


@router.post('/chat')
async def chat(request: Request):
    body = await request.json()
    message = body.get('message', '')
    if not message:
        raise HTTPException(status_code=400, detail='message is required')

    # Simple chat backend: echo the message and include output from `portfolio-mcp-server list-tools`
    reply_parts = []
    reply_parts.append(f"You said: {message}")

    async def run_list_tools():
        cmd = ['portfolio-mcp-server', 'list-tools']
        try:
            proc = await anyio.to_thread.run_sync(lambda: subprocess.run(cmd, capture_output=True, text=True, check=False))
            out = proc.stdout.strip()
            err = proc.stderr.strip()
            if out:
                reply_parts.append('Tools:\n' + out)
            if err:
                reply_parts.append('Errors:\n' + err)
        except Exception as e:
            reply_parts.append('Failed to run list-tools: ' + str(e))

    await run_list_tools()

    return { 'reply': '\n\n'.join(reply_parts) }
