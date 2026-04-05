import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Text, ForeignKey
from app.core.database import Base
import enum

class CredentialType(str, enum.Enum):
    TITLE = "title"
    LICENSE = "license"
    SPECIALTY = "specialty"
    COURSE = "course"
    OTHER = "other"

class VerifiedStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class ProfessionalCredential(Base):
    __tablename__ = "professional_credentials"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    professional_id = Column(String, nullable=False, index=True)
    credential_type = Column(SQLEnum(CredentialType), nullable=False)
    title = Column(String, nullable=False)
    issuing_entity = Column(String, nullable=False)
    credential_number = Column(String, nullable=True)
    issue_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    verified_status = Column(SQLEnum(VerifiedStatus), default=VerifiedStatus.PENDING)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    deleted_by = Column(String, nullable=True)
    version = Column(String, default="1")

class DocumentType(str, enum.Enum):
    NATIONAL_ID_FRONT = "national_id_front"
    NATIONAL_ID_BACK = "national_id_back"
    DEGREE = "degree"
    REGISTRATION_CERTIFICATE = "registration_certificate"
    SELFIE_VERIFICATION = "selfie_verification"
    CV = "cv"
    SIGNED_AGREEMENT = "signed_agreement"
    SUPPORTING_DOCUMENT = "supporting_document"

class ReviewStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class ProfessionalDocument(Base):
    __tablename__ = "professional_documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    professional_id = Column(String, nullable=False, index=True)
    document_type = Column(SQLEnum(DocumentType), nullable=False)
    file_id = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    sha256 = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    review_status = Column(SQLEnum(ReviewStatus), default=ReviewStatus.PENDING)
    review_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    deleted_by = Column(String, nullable=True)
    version = Column(String, default="1")