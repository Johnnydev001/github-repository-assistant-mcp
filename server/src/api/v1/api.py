from fastapi import APIRouter, HTTPException
from pathlib import Path

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[3]

@router.get("/read-file")
async def read_file(path: str):
    return {"output": "test"}


@router.get("/file-history")
async def get_file_history(file_name: str, branch: str = "main"):
    return {"output": "test"}
