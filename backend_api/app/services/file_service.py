import hashlib
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.file import AccessLevel, File, StorageBackend


class FileService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.base_path = Path(settings.FILES_PATH).resolve()

    async def save_upload(
        self,
        *,
        upload: UploadFile,
        owner_user_id: str,
        relative_dir: str,
        access_level: AccessLevel = AccessLevel.SENSITIVE,
    ) -> tuple[File, bytes]:
        content = await upload.read()
        sha256 = hashlib.sha256(content).hexdigest()
        extension = Path(upload.filename or "upload.bin").suffix
        relative_path = Path(relative_dir) / f"{uuid.uuid4()}{extension}"
        absolute_path = self.base_path / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_bytes(content)

        file_record = File(
            id=str(uuid.uuid4()),
            storage_backend=StorageBackend.LOCAL,
            relative_path=relative_path.as_posix(),
            original_filename=upload.filename or "upload.bin",
            mime_type=upload.content_type or "application/octet-stream",
            size_bytes=str(len(content)),
            sha256=sha256,
            access_level=access_level,
            owner_user_id=owner_user_id,
        )
        self.db.add(file_record)
        await self.db.flush()
        await upload.seek(0)
        return file_record, content

    def move_to_deleted(self, relative_path: str) -> str:
        source_path = self.base_path / relative_path
        deleted_path = self.base_path / "_deleted" / relative_path
        deleted_path.parent.mkdir(parents=True, exist_ok=True)

        if source_path.exists():
            shutil.move(str(source_path), str(deleted_path))

        return deleted_path.relative_to(self.base_path).as_posix()

    async def delete_file(self, file_id: str, deleted_by: str) -> bool:
        """
        Soft delete a file record and move physical file to _deleted folder.

        Returns:
            bool: True if deleted, False if file not found
        """
        from sqlalchemy import select
        result = await self.db.execute(select(File).where(File.id == file_id))
        file_record = result.scalar_one_or_none()

        if not file_record or file_record.deleted_at is not None:
            return False

        file_record.deleted_at = datetime.utcnow()
        file_record.deleted_by = deleted_by

        self.move_to_deleted(file_record.relative_path)

        await self.db.flush()
        return True
