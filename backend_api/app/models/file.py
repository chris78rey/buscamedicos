import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Text
from app.core.database import Base
import enum

class StorageBackend(str, enum.Enum):
    LOCAL = "local"

class AccessLevel(str, enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    SENSITIVE = "sensitive"

class SubjectType(str, enum.Enum):
    USER = "user"
    ROLE = "role"

class Permission(str, enum.Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    GRANT = "grant"

class File(Base):
    __tablename__ = "files"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    storage_backend = Column(SQLEnum(StorageBackend), default=StorageBackend.LOCAL)
    relative_path = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    size_bytes = Column(String, nullable=False)
    sha256 = Column(String, nullable=False)
    is_encrypted = Column(String, default="false")
    access_level = Column(SQLEnum(AccessLevel), default=AccessLevel.PRIVATE)
    owner_user_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(String, nullable=True)

class FilePermission(Base):
    __tablename__ = "file_permissions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    file_id = Column(String, nullable=False, index=True)
    subject_type = Column(SQLEnum(SubjectType), nullable=False)
    subject_id = Column(String, nullable=False)
    permission = Column(SQLEnum(Permission), nullable=False)
    granted_by = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)