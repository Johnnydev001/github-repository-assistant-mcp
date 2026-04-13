from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from config import Settings
from github_client import GitHubRepositoryClient
from security import normalize_repo_path

settings = Settings.load()
github_client = GitHubRepositoryClient(
    owner=settings.portfolio_repo_owner,
    repo=settings.portfolio_repo_name,
    token=settings.github_token,
    ref=settings.portfolio_repo_ref,
)
mcp = FastMCP("portfolio-repository")


@mcp.tool()
def read_file(relative_path: str) -> str:
    """Read a UTF-8 text file from the configured GitHub repository."""
    normalized_path = normalize_repo_path(relative_path)
    return github_client.read_text_file(normalized_path)


def main() -> None:
    print("Started MCP server for portfolio repository. Listening for requests...")
    mcp.run()


if __name__ == "__main__":
    main()
