from __future__ import annotations

from pathlib import PurePosixPath


def normalize_repo_path(relative_path: str) -> str:
    if not relative_path:
        raise ValueError("relative_path must not be empty")

    candidate = PurePosixPath(relative_path)
    if candidate.is_absolute():
        raise ValueError("relative_path must not be absolute")
    if any(part == ".." for part in candidate.parts):
        raise ValueError("relative_path must not escape repository root")

    normalized = candidate.as_posix()
    if normalized in {"", "."}:
        raise ValueError("relative_path must point to a file")
    return normalized
