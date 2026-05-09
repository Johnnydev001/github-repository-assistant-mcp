from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import sys
from urllib.parse import urlparse


def _load_dotenv(dotenv_path: Path) -> None:
    if not dotenv_path.is_file():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        os.environ.setdefault(key, value)


@dataclass(frozen=True)
class Settings:
    repo_url: str
    repo_owner: str
    repo_name: str
    github_token: str
    repo_ref: str | None
    local_source_dir: Path | None

    @classmethod
    def load(cls) -> "Settings":
        project_root = Path(__file__).resolve().parents[1]
        _load_dotenv(project_root / ".env")

        raw_repo_url = os.environ.get("REPO_URL") or os.environ.get("repo_url")
        if not raw_repo_url:
            raise RuntimeError(
                "REPO_URL is not set. Configure it in your environment or .env."
            )

        parsed_url = urlparse(raw_repo_url)
        if parsed_url.scheme != "https" or parsed_url.netloc != "github.com":
            raise RuntimeError(
                "repo_url must be a GitHub HTTPS URL, for example "
                "https://github.com/your-user/your-private-repo.git"
            )

        repo_path_parts = parsed_url.path.strip("/").removesuffix(".git").split("/")
        if len(repo_path_parts) != 2 or not all(repo_path_parts):
            raise RuntimeError(
                "repo_url must point to a GitHub repository path like "
                "https://github.com/your-user/your-private-repo.git"
            )

        github_token = os.environ.get("GITHUB_TOKEN")
        if not github_token:
            raise RuntimeError(
                "GITHUB_TOKEN is not set. Configure a GitHub token with access to the "
                "private repository in your environment or .env."
            )

        repo_ref = os.environ.get("REPO_REF") or os.environ.get("repo_ref") or None
        raw_local_source_dir = os.environ.get("LOCAL_SOURCE_DIR") or None
        local_source_dir: Path | None = None
        if raw_local_source_dir:
            candidate = Path(raw_local_source_dir).expanduser()
            if candidate.exists() and candidate.is_dir():
                local_source_dir = candidate.resolve()
            else:
                # Heuristic fallback for containerized runs: if the provided path looks like
                # a host filesystem path (e.g., starts with /Users or contains the repo name),
                # map it to the container-local default path used by the Dockerfile.
                fallback = Path("/app/server/local_source")
                looks_like_host_path = (
                    raw_local_source_dir.startswith("/Users/")
                    or "repository-mcp-server" in raw_local_source_dir
                    or raw_local_source_dir.endswith("/server")
                )
                if looks_like_host_path and fallback.exists():
                    # Print a clear warning but continue using the container-local directory.
                    print(
                        f"WARNING: LOCAL_SOURCE_DIR '{raw_local_source_dir}' not found in container; "
                        f"falling back to '{fallback}'",
                        file=sys.stderr,
                    )
                    local_source_dir = fallback.resolve()
                else:
                    # Do not raise: make LOCAL_SOURCE_DIR optional. Only needed when
                    # source_relative_path is used during update-file calls.
                    print(
                        f"WARNING: Configured local source directory does not exist: {candidate}; "
                        "LOCAL_SOURCE_DIR will be ignored.",
                        file=sys.stderr,
                    )
                    local_source_dir = None

        return cls(
            repo_url=raw_repo_url,
            repo_owner=repo_path_parts[0],
            repo_name=repo_path_parts[1],
            github_token=github_token,
            repo_ref=repo_ref,
            local_source_dir=local_source_dir,
        )
