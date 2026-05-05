from fastapi import APIRouter, HTTPException, Request
from pathlib import Path
import json

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

    reply_parts = [f"You said: {message}"]

    # Use long-lived MCP ClientSession started at app startup
    mcp_session = getattr(request.app.state, 'mcp_session', None)
    if mcp_session is None:
        raise HTTPException(status_code=503, detail='MCP session not initialized')

    try:
        tools_result = await mcp_session.list_tools()
        tools = []
        for t in getattr(tools_result, 'tools', []) or []:
            name = getattr(t, 'name', None) or str(t)
            tools.append(name)
        if tools:
            reply_parts.append('Tools:\n' + '\n'.join(tools))
    except Exception as e:
        reply_parts.append('Failed to list tools: ' + str(e))

    return { 'reply': '\n\n'.join(reply_parts) }
