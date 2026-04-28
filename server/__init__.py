"""Server package shim to expose server/src as a package during local development."""
import os

# Ensure imports like `import server.github_client` find the modules placed under server/src
__path__.insert(0, os.path.join(os.path.dirname(__file__), "src"))
