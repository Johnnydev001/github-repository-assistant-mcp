from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
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
    portfolio_repo_url: str
    portfolio_repo_owner: str
    portfolio_repo_name: str
    github_token: str
    portfolio_repo_ref: str | None
    local_source_dir: Path | None

    @classmethod
    def load(cls) -> "Settings":
        project_root = Path(__file__).resolve().parents[1]
        _load_dotenv(project_root / ".env")

        raw_repo_url = os.environ.get("PORTFOLIO_REPO_URL")
        if not raw_repo_url:
            raise RuntimeError(
                "PORTFOLIO_REPO_URL is not set. Configure it in your environment or .env."
            )

        parsed_url = urlparse(raw_repo_url)
        if parsed_url.scheme != "https" or parsed_url.netloc != "github.com":
            raise RuntimeError(
                "PORTFOLIO_REPO_URL must be a GitHub HTTPS URL, for example "
                "https://github.com/your-user/your-private-repo.git"
            )

        repo_path_parts = parsed_url.path.strip("/").removesuffix(".git").split("/")
        if len(repo_path_parts) != 2 or not all(repo_path_parts):
            raise RuntimeError(
                "PORTFOLIO_REPO_URL must point to a GitHub repository path like "
                "https://github.com/your-user/your-private-repo.git"
            )

        github_token = os.environ.get("GITHUB_TOKEN")
        if not github_token:
            raise RuntimeError(
                "GITHUB_TOKEN is not set. Configure a GitHub token with access to the "
                "private repository in your environment or .env."
            )

        repo_ref = os.environ.get("PORTFOLIO_REPO_REF") or None
        raw_local_source_dir = os.environ.get("LOCAL_SOURCE_DIR") or None
        local_source_dir: Path | None = None
        if raw_local_source_dir:
            local_source_dir = Path(raw_local_source_dir).expanduser().resolve()
            if not local_source_dir.exists():
                raise RuntimeError(
                    f"Configured local source directory does not exist: {local_source_dir}"
                )
            if not local_source_dir.is_dir():
                raise RuntimeError(
                    f"Configured local source directory is not a directory: {local_source_dir}"
                )

        return cls(
            portfolio_repo_url=raw_repo_url,
            portfolio_repo_owner=repo_path_parts[0],
            portfolio_repo_name=repo_path_parts[1],
            github_token=github_token,
            portfolio_repo_ref=repo_ref,
            local_source_dir=local_source_dir,
        )
