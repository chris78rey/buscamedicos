import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum
from app.core.database import Base
import enum

class UserStatus(str, enum.Enum):
    PENDING_EMAIL_VERIFICATION = "pending_email_verification"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    SOFT_DELETED = "soft_deleted"

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    is_email_verified = Column(Boolean, default=False)
    status = Column(SQLEnum(UserStatus), default=UserStatus.PENDING_EMAIL_VERIFICATION)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    deleted_by = Column(String, nullable=True)
    version = Column(String, default="1")