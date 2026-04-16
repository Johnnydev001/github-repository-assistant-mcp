from __future__ import annotations

from pathlib import Path, PurePosixPath


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


def resolve_local_source_path(source_root: Path, relative_path: str) -> Path:
    if not relative_path:
        raise ValueError("source_relative_path must not be empty")

    candidate = (source_root / relative_path).resolve()
    if candidate != source_root and source_root not in candidate.parents:
        raise ValueError("source_relative_path must stay inside LOCAL_SOURCE_DIR")
    if not candidate.exists():
        raise FileNotFoundError(f"Local source file does not exist: {candidate}")
    if not candidate.is_file():
        raise IsADirectoryError(f"Local source path is not a file: {candidate}")
    return candidate
