from fastapi import APIRouter
from server.src.services import file_service

router = APIRouter()

# Read file endpoint
@router.get("/read-file")
async def read_file_endpoint(path: str):
    return await file_service.read_file(path)

# Update file endpoint
@router.patch("/update-file")
async def update_file_endpoint(path: str, message: str, content: str, source_path: str | None = None):
    return await file_service.update_file(path, message, content, source_path)

# Delete file endpoint
@router.delete("/delete-file")
async def delete_file_endpoint(path: str, message: str):
    return await file_service.delete_file(path, message)

# Create pull request endpoint
@router.post("/create-pull-request")
async def create_pr_endpoint(title: str, head: str, base: str, body: str | None = None):
    return await file_service.create_pr(title, head, base, body)

# File history endpoint
@router.get("/file-history")
async def get_file_history_endpoint(path: str):
    return await file_service.get_file_history(path)
