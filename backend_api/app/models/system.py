import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Text
from app.core.database import Base
import enum

class ExceptionalAccessStatus(str, enum.Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REVOKED = "revoked"

class ExceptionalAccessRequest(Base):
    __tablename__ = "exceptional_access_requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    requester_user_id = Column(String, nullable=False, index=True)
    target_user_id = Column(String, nullable=True)
    resource_type = Column(String, nullable=False)
    resource_id = Column(String, nullable=True)
    reason = Column(Text, nullable=False)
    patient_authorization_file_id = Column(String, nullable=True)
    status = Column(SQLEnum(ExceptionalAccessStatus), default=ExceptionalAccessStatus.REQUESTED)
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    deleted_by = Column(String, nullable=True)
    version = Column(String, default="1")

class SystemParameter(Base):
    __tablename__ = "system_parameters"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String, unique=True, nullable=False, index=True)
    value_json = Column(Text, nullable=False)
    description = Column(String, nullable=True)
    is_secret = Column(String, default="false")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class FeatureFlag(Base):
    __tablename__ = "feature_flags"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String, unique=True, nullable=False, index=True)
    enabled = Column(String, default="false")
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EntityVersion(Base):
    __tablename__ = "entity_versions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type = Column(String, nullable=False, index=True)
    entity_id = Column(String, nullable=False, index=True)
    version = Column(String, nullable=False)
    changed_by = Column(String, nullable=True)
    changed_at = Column(DateTime, default=datetime.utcnow)
    change_type = Column(String, nullable=False)
    before_json = Column(Text, nullable=True)
    after_json = Column(Text, nullable=True)