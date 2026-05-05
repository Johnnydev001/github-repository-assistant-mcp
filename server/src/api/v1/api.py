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
    message = (body.get('message', '') or '').strip()
    if not message:
        raise HTTPException(status_code=400, detail='message is required')

    # Use long-lived MCP ClientSession started at app startup
    mcp_session = getattr(request.app.state, 'mcp_session', None)
    if mcp_session is None:
        raise HTTPException(status_code=503, detail='MCP session not initialized')

    import re

    async def render_tool_result(result) -> str:
        content = getattr(result, 'content', None)
        if not content:
            return str(result)
        parts = []
        for item in content:
            text = getattr(item, 'text', None)
            if text is not None:
                parts.append(text)
                continue
            dumped = item.model_dump(mode='json') if hasattr(item, 'model_dump') else str(item)
            parts.append(json.dumps(dumped, indent=2))
        return '\n'.join(parts)

    # Simple NL parsing rules
    # read file: "read <path>" or "read file <path>"
    m = re.match(r'^(?:read|show)\s+(?:file\s+)?(.+)$', message, re.I)
    if m:
        path = m.group(1).strip()
        try:
            result = await mcp_session.call_tool('read_file', {'relative_path': path})
            reply = await render_tool_result(result)
            return {'reply': reply}
        except Exception as e:
            return {'reply': f'Error calling read_file: {e}'}

    # file history: "history of <path>" or contains "history"
    m = re.search(r'(?:history|log)\s+(?:of\s+)?(.+)$', message, re.I)
    if m:
        path = m.group(1).strip()
        try:
            result = await mcp_session.call_tool('get_file_history', {'file_name': path, 'branch': 'main'})
            reply = await render_tool_result(result)
            return {'reply': reply}
        except Exception as e:
            return {'reply': f'Error calling get_file_history: {e}'}

    # update file: "update <path> with <content>" or "write <content> to <path>"
    m = re.match(r'^(?:update|write|set)\s+(.+?)\s+(?:with|to)\s+(.+)$', message, re.I)
    if m:
        path = m.group(1).strip()
        content = m.group(2).strip()
        try:
            result = await mcp_session.call_tool('update_file', {'relative_path': path, 'commit_message': 'update via chat', 'content': content})
            reply = await render_tool_result(result)
            return {'reply': reply}
        except Exception as e:
            return {'reply': f'Error calling update_file: {e}'}

    # fallback: list tools and echo
    reply_parts = [f'You said: {message}']
    try:
        tools_result = await mcp_session.list_tools()
        tools = []
        for t in getattr(tools_result, 'tools', []) or []:
            name = getattr(t, 'name', None) or str(t)
            tools.append(name)
        if tools:
            reply_parts.append('Available tools:\n' + '\n'.join(tools))
    except Exception as e:
        reply_parts.append('Failed to list tools: ' + str(e))

    return {'reply': '\n\n'.join(reply_parts)}
