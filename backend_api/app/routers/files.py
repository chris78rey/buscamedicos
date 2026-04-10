from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.file import File
from app.models.user import User
from app.services.file_storage_service import FileStorageService

router = APIRouter(tags=["files"])


def _can_access_file(user: User, file_record: File) -> bool:
    if user.id == file_record.owner_user_id:
        return True
    try:
        role_codes = [r.code for r in user.roles]
    except Exception:
        role_codes = []
    if any(r in role_codes for r in ["super_admin", "admin_validation"]):
        return True
    return False


@router.get("/{file_id}/meta")
async def get_file_metadata(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(File).where(File.id == file_id))
    file_record = result.scalar_one_or_none()
    
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    if file_record.deleted_at:
        raise HTTPException(status_code=404, detail="File not found")
    
    if not _can_access_file(current_user, file_record):
        raise HTTPException(status_code=403, detail="Access denied")
    
    storage = FileStorageService()
    physical_exists = storage.file_exists(file_record.relative_path)
    
    return {
        "id": str(file_record.id),
        "original_filename": file_record.original_filename,
        "mime_type": file_record.mime_type,
        "size_bytes": file_record.size_bytes,
        "sha256": file_record.sha256,
        "physical_exists": physical_exists,
        "created_at": file_record.created_at.isoformat() if file_record.created_at else None,
    }


@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(File).where(File.id == file_id))
    file_record = result.scalar_one_or_none()
    
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    if file_record.deleted_at:
        raise HTTPException(status_code=404, detail="File not found")
    
    if not _can_access_file(current_user, file_record):
        raise HTTPException(status_code=403, detail="Access denied")
    
    storage = FileStorageService()
    file_path = storage.get_absolute_path(file_record.relative_path)
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Physical file not found on server")
    
    return FileResponse(
        path=str(file_path),
        filename=file_record.original_filename,
        media_type=file_record.mime_type,
    )
