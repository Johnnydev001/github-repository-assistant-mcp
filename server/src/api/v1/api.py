from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pathlib import Path
import json

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[3]

@router.get("/list-tools")
async def list_tools():
    return {"output": "test"}

@router.get("/read-file")
async def read_file(path: str):
    return {"output": "test"}


@router.get("/file-history")
async def get_file_history(file_name: str, branch: str = "main"):
    return {"output": "test"}
