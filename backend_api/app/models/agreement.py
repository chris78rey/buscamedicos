import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Text, Boolean
from app.core.database import Base
import enum

class AgreementType(str, enum.Enum):
    PLATFORM_TERMS = "platform_terms"
    PRIVACY_POLICY = "privacy_policy"
    PROFESSIONAL_RESPONSIBILITY_AGREEMENT = "professional_responsibility_agreement"

class AcceptanceType(str, enum.Enum):
    CLICKWRAP = "clickwrap"
    ELECTRONIC_SIGNATURE = "electronic_signature"
    EQUIVALENT_FORMAL_MECHANISM = "equivalent_formal_mechanism"

class AgreementAcceptanceStatus(str, enum.Enum):
    ACCEPTED = "accepted"
    REVOKED = "revoked"

class Agreement(Base):
    __tablename__ = "agreements"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agreement_type = Column(SQLEnum(AgreementType), nullable=False, index=True)
    version_code = Column(String, nullable=False)
    title = Column(String, nullable=False)
    content_markdown = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    published_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    deleted_by = Column(String, nullable=True)
    version = Column(String, default="1")

class AgreementAcceptance(Base):
    __tablename__ = "agreement_acceptances"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agreement_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    accepted_at = Column(DateTime, default=datetime.utcnow)
    acceptance_type = Column(SQLEnum(AcceptanceType), nullable=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    evidence_file_id = Column(String, nullable=True)
    status = Column(SQLEnum(AgreementAcceptanceStatus), default=AgreementAcceptanceStatus.ACCEPTED)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    deleted_by = Column(String, nullable=True)
    version = Column(String, default="1")