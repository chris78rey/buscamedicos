import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Text, ForeignKey
from app.core.database import Base
import enum

class VerificationRequestStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_CORRECTION = "needs_correction"
    SUSPENDED = "suspended"

class VerificationEventType(str, enum.Enum):
    SUBMITTED = "submitted"
    ASSIGNED = "assigned"
    COMMENT_ADDED = "comment_added"
    DOCUMENT_APPROVED = "document_approved"
    DOCUMENT_REJECTED = "document_rejected"
    APPROVED = "approved"
    REJECTED = "rejected"
    CORRECTION_REQUESTED = "correction_requested"
    SUSPENDED = "suspended"

class VerificationRequest(Base):
    __tablename__ = "verification_requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    professional_id = Column(String, nullable=False, index=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    assigned_admin_id = Column(String, nullable=True)
    status = Column(SQLEnum(VerificationRequestStatus), default=VerificationRequestStatus.SUBMITTED)
    decision_at = Column(DateTime, nullable=True)
    decision_reason = Column(Text, nullable=True)
    reviewed_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    deleted_by = Column(String, nullable=True)
    version = Column(String, default="1")

class VerificationEvent(Base):
    __tablename__ = "verification_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    verification_request_id = Column(String, nullable=False, index=True)
    event_type = Column(SQLEnum(VerificationEventType), nullable=False)
    event_payload_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=True)