from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from config import Settings
from github_client import GitHubRepositoryClient
from security import normalize_repo_path, resolve_local_source_path

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


@mcp.tool()
def update_file(
    relative_path: str,
    commit_message: str,
    content: str | None = None,
    source_relative_path: str | None = None,
) -> str:
    """Update or create a file in the configured GitHub repository."""
    normalized_path = normalize_repo_path(relative_path)
    file_content = _resolve_update_content(content, source_relative_path)
    result = github_client.update_file_content(
        normalized_path,
        content=file_content,
        commit_message=commit_message,
    )
    return json.dumps(result, indent=2)


@mcp.tool()
def delete_file(relative_path: str, commit_message: str) -> str:
    """Delete a file from the configured GitHub repository."""
    normalized_path = normalize_repo_path(relative_path)
    result = github_client.delete_file(
        normalized_path,
        commit_message=commit_message,
    )
    return json.dumps(result, indent=2)


def _resolve_update_content(
    inline_content: str | None,
    source_relative_path: str | None,
) -> bytes:
    if (inline_content is None) == (source_relative_path is None):
        raise ValueError("Provide exactly one of content or source_relative_path")

    if inline_content is not None:
        return inline_content.encode("utf-8")

    if settings.local_source_dir is None:
        raise RuntimeError(
            "LOCAL_SOURCE_DIR is not configured. It is required when using "
            "source_relative_path."
        )

    source_path = resolve_local_source_path(settings.local_source_dir, source_relative_path or "")
    return source_path.read_bytes()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
