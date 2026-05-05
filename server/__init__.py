"""Server package shim to expose server/src as a package during local development.

This shim makes `from server import main` work in the installed console_script by
re-exporting the main entrypoint from the server module inside server/src.
"""
import os

# Ensure imports like `import server.github_client` find the modules placed under server/src
__path__.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Re-export main and common symbols from server/server.py so console scripts can use "server:main"
try:
    from .server import main, settings, mcp  # type: ignore
except Exception:
    # Import failures are handled at runtime; keep shim lightweight and fail later with clear errors
    pass
