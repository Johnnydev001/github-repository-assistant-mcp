from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pathlib import Path
import json
import re
import time
import uuid

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# Intent detection helpers
# ---------------------------------------------------------------------------

def _extract_last_user_message(body: dict) -> str:
    messages = body.get("messages") or body.get("input") or []
    if isinstance(messages, list):
        for m in reversed(messages):
            if isinstance(m, dict) and m.get("role") == "user" and m.get("content"):
                return str(m["content"])
    if isinstance(messages, str):
        return messages
    return ""


def _detect_intent(text: str) -> dict:
    """Return intent dict: {action, params}"""
    t = text.strip()

    # --- list_tools ---
    if re.search(r'\blist\b.*\btools?\b|\btools?\b.*\blist\b|what can you do|available tools?', t, re.I):
        return {"action": "list_tools", "params": {}}

    # --- read_file ---
    m = re.search(r'\bread\b.*?["\']?([^\s"\']+\.[a-zA-Z0-9]+)["\']?', t, re.I)
    if m:
        return {"action": "read_file", "params": {"relative_path": m.group(1)}}

    # --- update_file ---
    m = re.search(r'\bupdate\b.*?["\']?([^\s"\']+\.[a-zA-Z0-9]+)["\']?', t, re.I)
    if m:
        path = m.group(1)
        # Try to extract inline content after "with:" or "content:" or "set to"
        content_m = re.search(r'(?:with|content:|set to)[:\s]+["\']?(.+)["\']?$', t, re.I)
        content = content_m.group(1).strip() if content_m else ""
        commit_m = re.search(r'(?:commit[:\s]+)["\']?(.+?)["\']?(?:\s+content|$)', t, re.I)
        commit_msg = commit_m.group(1).strip() if commit_m else f"Update {path}"
        return {
            "action": "update_file",
            "params": {"relative_path": path, "commit_message": commit_msg, "content": content or None},
        }

    # --- delete_file ---
    m = re.search(r'\bdelete\b.*?["\']?([^\s"\']+\.[a-zA-Z0-9]+)["\']?', t, re.I)
    if m:
        path = m.group(1)
        commit_m = re.search(r'commit[:\s]+["\']?(.+?)["\']?$', t, re.I)
        commit_msg = commit_m.group(1).strip() if commit_m else f"Delete {path}"
        return {
            "action": "delete_file",
            "params": {"relative_path": path, "commit_message": commit_msg},
        }

    # --- create_pull_request ---
    if re.search(r'\bcreate\b.*\bpr\b|\bcreate\b.*\bpull.?request\b|\bopen\b.*\bpr\b', t, re.I):
        title_m = re.search(r'(?:title[:\s]+)["\']?(.+?)["\']?(?:\s+from|\s+head|\s+base|$)', t, re.I)
        head_m = re.search(r'\bfrom\b\s+["\']?(\S+)["\']?', t, re.I) or re.search(r'\bhead\b[:\s]+["\']?(\S+)["\']?', t, re.I)
        base_m = re.search(r'\binto\b\s+["\']?(\S+)["\']?', t, re.I) or re.search(r'\bbase\b[:\s]+["\']?(\S+)["\']?', t, re.I)
        return {
            "action": "create_pull_request",
            "params": {
                "title": title_m.group(1).strip() if title_m else t[:80],
                "head": head_m.group(1).strip() if head_m else "feature-branch",
                "base": base_m.group(1).strip() if base_m else "main",
                "body": t,
            },
        }

    return {"action": "unknown", "params": {}}


def _make_completion(content: str, model: str = "mcp-assistant") -> dict:
    return {
        "id": str(uuid.uuid4()),
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/health")
async def health(request: Request):
    session = getattr(request.app.state, "mcp_session", None)
    return JSONResponse(content={
        "status": "ok" if session is not None else "degraded",
        "mcp_session": session is not None,
    })


@router.get("/list-tools")
async def list_tools_get(request: Request):
    mcp_session = getattr(request.app.state, "mcp_session", None)
    if mcp_session is None:
        return JSONResponse(status_code=503, content={"error": "MCP session not initialized"})
    result = await mcp_session.list_tools()
    tools = [getattr(t, "name", str(t)) for t in (getattr(result, "tools", []) or [])]
    return {"tools": tools}


@router.post("/assistant")
async def assistant(request: Request):
    """AssistantUI-compatible endpoint. Detects intent from the last user message
    and dispatches to the appropriate MCP tool (list_tools, read_file,
    update_file, delete_file, create_pull_request).
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "invalid json"})

    mcp_session = getattr(request.app.state, "mcp_session", None)
    if mcp_session is None:
        return JSONResponse(status_code=503, content={"error": "MCP session not initialized"})

    last_user = _extract_last_user_message(body)
    intent = _detect_intent(last_user)
    action = intent["action"]
    params = intent["params"]

    try:
        # ---- list_tools ----
        if action == "list_tools":
            result = await mcp_session.list_tools()
            tools = [getattr(t, "name", str(t)) for t in (getattr(result, "tools", []) or [])]
            reply = "Available MCP tools:\n" + "\n".join(f"- {t}" for t in tools)

        # ---- read_file ----
        elif action == "read_file":
            path = params.get("relative_path", "")
            if not path:
                reply = "Please specify a file path to read (e.g. 'read README.md')."
            else:
                result = await mcp_session.call_tool("read_file", {"relative_path": path})
                content = _extract_tool_text(result)
                reply = f"**{path}**\n\n```\n{content}\n```"

        # ---- update_file ----
        elif action == "update_file":
            path = params.get("relative_path", "")
            content = params.get("content")
            commit_msg = params.get("commit_message", f"Update {path}")
            if not path or content is None:
                reply = (
                    "To update a file please provide:\n"
                    "- file path\n- commit message\n- new content\n\n"
                    "Example: *update README.md commit: fix typo content: new text here*"
                )
            else:
                result = await mcp_session.call_tool(
                    "update_file",
                    {"relative_path": path, "commit_message": commit_msg, "content": content},
                )
                reply = f"File **{path}** updated.\n\n{_extract_tool_text(result)}"

        # ---- delete_file ----
        elif action == "delete_file":
            path = params.get("relative_path", "")
            commit_msg = params.get("commit_message", f"Delete {path}")
            if not path:
                reply = "Please specify a file path to delete (e.g. 'delete old/file.md')."
            else:
                result = await mcp_session.call_tool(
                    "delete_file",
                    {"relative_path": path, "commit_message": commit_msg},
                )
                reply = f"File **{path}** deleted.\n\n{_extract_tool_text(result)}"

        # ---- create_pull_request ----
        elif action == "create_pull_request":
            result = await mcp_session.call_tool("create_pull_request", params)
            reply = f"Pull request created.\n\n{_extract_tool_text(result)}"

        # ---- unknown / fallback ----
        else:
            result = await mcp_session.list_tools()
            tools = [getattr(t, "name", str(t)) for t in (getattr(result, "tools", []) or [])]
            reply = (
                "I didn't understand that request. Here are the things I can do:\n\n"
                + "\n".join(f"- **{t}**" for t in tools)
                + "\n\nTry: *list tools*, *read README.md*, *delete old.md*, "
                "*update file.md commit: msg content: text*, or *create pr title: ... from: branch into: main*"
            )

    except Exception as exc:
        reply = f"Error executing `{action}`: {exc}"

    return JSONResponse(content=_make_completion(reply))


def _extract_tool_text(result) -> str:
    """Pull plain text out of an MCP CallToolResult."""
    contents = getattr(result, "content", None) or []
    parts = []
    for c in contents:
        text = getattr(c, "text", None)
        if text:
            parts.append(text)
    return "\n".join(parts) if parts else str(result)

