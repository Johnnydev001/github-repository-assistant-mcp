"""Package shim exposing server.main for console-scripts
"""
from .server import main, settings, mcp

__all__ = ["main", "settings", "mcp"]
