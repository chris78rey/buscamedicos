import hashlib
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional, Tuple

from fastapi import UploadFile

from app.core.config import settings
from app.models.file import AccessLevel, File, StorageBackend


class FileStorageService:
    def __init__(self):
        self.base_path = Path(settings.FILES_PATH).resolve()
        self._ensure_base_dir()

    def _ensure_base_dir(self) -> None:
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _validate_extension(self, filename: str, forced_ext: Optional[str] = None) -> str:
        ext = forced_ext or Path(filename).suffix.lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise ValueError(f"Extension {ext} not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}")
        return ext

    def _validate_mime_type(self, mime_type: str, forced_pdf: bool = False) -> str:
        if forced_pdf and mime_type != "application/pdf":
            raise ValueError("This document type requires PDF format")
        if mime_type not in settings.ALLOWED_MIME_TYPES:
            raise ValueError(f"MIME type {mime_type} not allowed. Allowed: {settings.ALLOWED_MIME_TYPES}")
        return mime_type

    def _validate_size(self, content: bytes) -> int:
        size_mb = len(content) / (1024 * 1024)
        if size_mb > settings.MAX_FILE_SIZE_MB:
            raise ValueError(f"File size {size_mb:.2f}MB exceeds maximum {settings.MAX_FILE_SIZE_MB}MB")
        return len(content)

    async def save_professional_document(
        self,
        upload: UploadFile,
        professional_id: str,
        document_type: str,
        owner_user_id: str,
        force_pdf: bool = False,
    ) -> Tuple[File, bytes]:
        content = await upload.read()
        
        ext = self._validate_extension(upload.filename or "file.pdf", ".pdf" if force_pdf else None)
        mime = self._validate_mime_type(upload.content_type or "application/pdf", force_pdf)
        size = self._validate_size(content)
        
        sha256_hash = hashlib.sha256(content).hexdigest()
        
        file_id = str(uuid.uuid4())
        relative_path = Path("professional_documents") / professional_id / document_type / f"{file_id}{ext}"
        absolute_path = self.base_path / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_bytes(content)

        file_record = File(
            id=file_id,
            storage_backend=StorageBackend.LOCAL,
            relative_path=relative_path.as_posix(),
            original_filename=upload.filename or f"document{ext}",
            mime_type=mime,
            size_bytes=str(size),
            sha256=sha256_hash,
            is_encrypted="false",
            access_level=AccessLevel.PRIVATE,
            owner_user_id=owner_user_id,
        )
        
        await upload.seek(0)
        return file_record, content

    def get_absolute_path(self, relative_path: str) -> Path:
        return self.base_path / relative_path

    def file_exists(self, relative_path: str) -> bool:
        return self.get_absolute_path(relative_path).exists()

    def soft_delete_file(self, relative_path: str) -> Optional[str]:
        source = self.get_absolute_path(relative_path)
        if not source.exists():
            return None
        
        now = "_deleted"
        parts = relative_path.split("/")
        deleted_relative = Path(now) / "/".join(parts)
        dest = self.base_path / deleted_relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(dest))
        
        return deleted_relative.as_posix()
