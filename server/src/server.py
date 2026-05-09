from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP
from typing import Optional
import sys

from config import Settings
from github_client import GitHubRepositoryClient
from security import normalize_repo_path, resolve_local_source_path

# Defer loading Settings and GitHub client until runtime to avoid failures
# when importing this module in containerized environments where host
# LOCAL_SOURCE_DIR may not exist. Use lazy initialization in ensure_initialized().
settings: Optional[Settings] = None
github_client: Optional[GitHubRepositoryClient] = None

mcp = FastMCP("portfolio-repository")


def ensure_initialized() -> None:
    global settings, github_client
    if settings is None:
        settings = Settings.load()
    if github_client is None:
        github_client = GitHubRepositoryClient(
            owner=settings.portfolio_repo_owner,  # type: ignore[arg-type]
            repo=settings.portfolio_repo_name,  # type: ignore[arg-type]
            token=settings.github_token,  # type: ignore[arg-type]
            ref=settings.portfolio_repo_ref,  # type: ignore[arg-type]
        )


@mcp.tool()
def read_file(relative_path: str) -> str:
    """Read a UTF-8 text file from the configured GitHub repository."""
    ensure_initialized()
    normalized_path = normalize_repo_path(relative_path)
    # type: ignore[var-annotated]
    return github_client.read_text_file(normalized_path)


@mcp.tool()
def update_file(
    relative_path: str,
    commit_message: str,
    content: str | None = None,
    source_relative_path: str | None = None,
) -> str:
    """Update or create a file in the configured GitHub repository."""
    ensure_initialized()
    normalized_path = normalize_repo_path(relative_path)
    file_content = _resolve_update_content(content, source_relative_path)
    # type: ignore[var-annotated]
    result = github_client.update_file_content(
        normalized_path,
        content=file_content,
        commit_message=commit_message,
    )
    return json.dumps(result, indent=2)


@mcp.tool()
def delete_file(relative_path: str, commit_message: str) -> str:
    """Delete a file from the configured GitHub repository."""
    ensure_initialized()
    normalized_path = normalize_repo_path(relative_path)
    # type: ignore[var-annotated]
    result = github_client.delete_file(
        normalized_path,
        commit_message=commit_message,
    )
    return json.dumps(result, indent=2)


@mcp.tool()
def get_file_history(file_name: str, branch: str = "main") -> str:
    """Get the commit history for a file in the configured GitHub repository."""
    ensure_initialized()
    # type: ignore[var-annotated]
    result = github_client.get_file_history(file_name=file_name, branch=branch)
    serializable = [vars(c) for c in result]
    return json.dumps(serializable, indent=2)

@mcp.tool()
def create_pull_request(
    title: str,
    head: str,
    base: str,
    body: str | None = None,
) -> str:
    """Create a pull request on the configured repository.
    """
    ensure_initialized()
    # type: ignore[var-annotated]
    result = github_client.create_pull_request(
        title=title,
        head=head,
        base=base,
        body=body,
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

    # Ensure settings are initialized so local_source_dir is available
    ensure_initialized()
    if settings.local_source_dir is None:
        raise RuntimeError(
            "LOCAL_SOURCE_DIR is not configured. It is required when using "
            "source_relative_path."
        )

    source_path = resolve_local_source_path(settings.local_source_dir, source_relative_path or "")
    return source_path.read_bytes()


def main() -> None:
    ensure_initialized()
    mcp.run()


if __name__ == "__main__":
    main()
