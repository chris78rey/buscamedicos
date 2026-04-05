import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Boolean, Text
from app.core.database import Base
import enum

class OnboardingStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"

class ProfessionalStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    ACTIVE = "active"
    REJECTED = "rejected"
    SUSPENDED = "suspended"

class Professional(Base):
    __tablename__ = "professionals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, unique=True, nullable=False, index=True)
    person_id = Column(String, unique=True, nullable=False, index=True)
    public_slug = Column(String, unique=True, nullable=True, index=True)
    professional_type = Column(String, nullable=True)
    public_display_name = Column(String, nullable=True)
    bio_public = Column(Text, nullable=True)
    years_experience = Column(String, nullable=True)
    languages_json = Column(String, nullable=True)
    onboarding_status = Column(SQLEnum(OnboardingStatus), default=OnboardingStatus.DRAFT)
    is_public_profile_enabled = Column(Boolean, default=False)
    status = Column(SQLEnum(ProfessionalStatus), default=ProfessionalStatus.DRAFT)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    deleted_by = Column(String, nullable=True)
    version = Column(String, default="1")