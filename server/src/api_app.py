"""ASGI FastAPI application separate from the MCP server."""
from fastapi import FastAPI
from api.v1.api import router

app = FastAPI(title="Portfolio MCP Server API")
app.include_router(router, prefix="/api")
