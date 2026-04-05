import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, ForeignKey
from app.core.database import Base
import enum

class VerificationLevel(str, enum.Enum):
    BASIC = "basic"
    IDENTITY_VERIFIED = "identity_verified"

class PatientStatus(str, enum.Enum):
    ACTIVE = "active"
    RESTRICTED = "restricted"
    SUSPENDED = "suspended"

class Patient(Base):
    __tablename__ = "patients"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, unique=True, nullable=False, index=True)
    person_id = Column(String, unique=True, nullable=False, index=True)
    verification_level = Column(SQLEnum(VerificationLevel), default=VerificationLevel.BASIC)
    emergency_contact_name = Column(String, nullable=True)
    emergency_contact_phone = Column(String, nullable=True)
    status = Column(SQLEnum(PatientStatus), default=PatientStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    deleted_by = Column(String, nullable=True)
    version = Column(String, default="1")