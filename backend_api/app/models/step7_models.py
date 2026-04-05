import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, SmallInteger
from app.core.database import Base


class ClassificationCode:
    PUBLIC = "public"
    INTERNAL = "internal"
    PERSONAL = "personal"
    SENSITIVE_HEALTH = "sensitive_health"
    RESTRICTED_LEGAL = "restricted_legal"


class DataClassification(Base):
    __tablename__ = "data_classifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    severity_level = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")


class AccessMode:
    NORMAL = "normal"
    EXCEPTIONAL_ONLY = "exceptional_only"
    HYBRID = "hybrid"


class ResourceAccessPolicy(Base):
    __tablename__ = "resource_access_policies"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_type = Column(String, unique=True, nullable=False)
    classification_code = Column(String, nullable=False)
    access_mode = Column(String, nullable=False)
    requires_relationship = Column(Boolean, default=True)
    requires_patient_authorization = Column(Boolean, default=False)
    requires_justification = Column(Boolean, default=False)
    max_access_minutes = Column(Integer, nullable=True)
    allow_download = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")


class ConsentType:
    DATA_PROCESSING_HEALTH = "data_processing_health"
    EXCEPTIONAL_CLINICAL_ACCESS = "exceptional_clinical_access"
    DATA_EXPORT = "data_export"
    TELECONSULTATION = "teleconsultation"
    LAB_RESULT_SHARING = "lab_result_sharing"


class ConsentStatus:
    GRANTED = "granted"
    REVOKED = "revoked"
    EXPIRED = "expired"


class ConsentSource:
    CLICKWRAP = "clickwrap"
    SIGNED_FILE = "signed_file"
    RECORDED_CONFIRMATION = "recorded_confirmation"
    ADMIN_DOCUMENTED_BASIS = "admin_documented_basis"


class PatientPrivacyConsent(Base):
    __tablename__ = "patient_privacy_consents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, nullable=False, index=True)
    consent_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    granted_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    source = Column(String, nullable=False)
    evidence_file_id = Column(String, nullable=True)
    granted_by_user_id = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")


class ExceptionalAccessRequestStatus:
    REQUESTED = "requested"
    PENDING_PATIENT_AUTHORIZATION = "pending_patient_authorization"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REVOKED = "revoked"
    CONSUMED = "consumed"


class ScopeType:
    SINGLE_RESOURCE = "single_resource"
    APPOINTMENT_SCOPE = "appointment_scope"
    PATIENT_SCOPE_LIMITED = "patient_scope_limited"


class ExceptionalAccessRequest(Base):
    __tablename__ = "exceptional_access_requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    requester_user_id = Column(String, nullable=False, index=True)
    requester_role_code = Column(String, nullable=False)
    patient_id = Column(String, nullable=True, index=True)
    target_user_id = Column(String, nullable=True)
    resource_type = Column(String, nullable=False)
    resource_id = Column(String, nullable=True)
    scope_type = Column(String, nullable=False)
    justification = Column(Text, nullable=False)
    business_basis = Column(String, nullable=True)
    requested_minutes = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    requires_patient_authorization = Column(Boolean, default=False)
    patient_consent_id = Column(String, nullable=True)
    approved_by_user_id = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejected_by_user_id = Column(String, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    starts_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    revoked_by_user_id = Column(String, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    revoke_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")


class GrantStatus:
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    CONSUMED = "consumed"


class ExceptionalAccessGrant(Base):
    __tablename__ = "exceptional_access_grants"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id = Column(String, unique=True, nullable=False)
    grantee_user_id = Column(String, nullable=False, index=True)
    resource_type = Column(String, nullable=False)
    resource_id = Column(String, nullable=True)
    scope_type = Column(String, nullable=False)
    granted_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")


class ClinicalAccessMode:
    NORMAL = "normal"
    EXCEPTIONAL = "exceptional"


class ClinicalAccessAction:
    READ = "read"
    LIST = "list"
    DOWNLOAD = "download"
    EXPORT_META = "export_meta"


class ClinicalAccessDecision:
    ALLOWED = "allowed"
    DENIED = "denied"


class ClinicalAccessLog(Base):
    __tablename__ = "clinical_access_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_user_id = Column(String, nullable=False, index=True)
    actor_role_code = Column(String, nullable=False)
    patient_id = Column(String, nullable=True, index=True)
    target_user_id = Column(String, nullable=True)
    resource_type = Column(String, nullable=False)
    resource_id = Column(String, nullable=True)
    access_mode = Column(String, nullable=False)
    action = Column(String, nullable=False)
    decision = Column(String, nullable=False)
    policy_snapshot_json = Column(Text, nullable=True)
    exceptional_access_request_id = Column(String, nullable=True)
    justification = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    request_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ProcessingActivity(Base):
    __tablename__ = "processing_activities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String, unique=True, nullable=False)
    module_name = Column(String, nullable=False)
    purpose = Column(Text, nullable=False)
    data_categories_json = Column(Text, nullable=False)
    subject_categories_json = Column(Text, nullable=False)
    legal_basis = Column(Text, nullable=True)
    retention_policy_id = Column(String, nullable=True)
    is_sensitive = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")


class DeleteMode:
    SOFT_ONLY = "soft_only"
    SOFT_THEN_ARCHIVE = "soft_then_archive"


class RetentionPolicy(Base):
    __tablename__ = "retention_policies"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String, unique=True, nullable=False)
    resource_type = Column(String, nullable=False)
    retention_days = Column(Integer, nullable=True)
    archive_after_days = Column(Integer, nullable=True)
    delete_mode = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")


class IncidentSeverity:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentType:
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    OVEREXPOSURE = "overexposure"
    POLICY_VIOLATION = "policy_violation"
    EXPORT_VIOLATION = "export_violation"
    OTHER = "other"


class IncidentStatus:
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class PrivacyIncident(Base):
    __tablename__ = "privacy_incidents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_code = Column(String, unique=True, nullable=False)
    detected_at = Column(DateTime, nullable=False)
    reported_by_user_id = Column(String, nullable=True)
    severity = Column(String, nullable=False)
    incident_type = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    affected_resource_type = Column(String, nullable=True)
    affected_resource_id = Column(String, nullable=True)
    status = Column(String, nullable=False)
    assigned_admin_id = Column(String, nullable=True)
    resolution_summary = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")


class IncidentEventType:
    OPENED = "opened"
    ASSIGNED = "assigned"
    CONTAINED = "contained"
    NOTE_ADDED = "note_added"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class PrivacyIncidentEvent(Base):
    __tablename__ = "privacy_incident_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    privacy_incident_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    event_payload_json = Column(Text, nullable=True)
    created_by_user_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class PrivacyPolicyType:
    PATIENT_PRIVACY = "patient_privacy"
    PROFESSIONAL_PRIVACY = "professional_privacy"
    INTERNAL_ACCESS_POLICY = "internal_access_policy"
    RETENTION_POLICY = "retention_policy"


class PrivacyPolicyVersion(Base):
    __tablename__ = "privacy_policy_versions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_type = Column(String, nullable=False)
    version_code = Column(String, nullable=False)
    content_markdown = Column(Text, nullable=False)
    is_active = Column(Boolean, default=False)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")


class AcceptanceStatus:
    ACCEPTED = "accepted"
    SUPERSEDED = "superseded"


class PrivacyPolicyAcceptance(Base):
    __tablename__ = "privacy_policy_acceptances"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_version_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    accepted_at = Column(DateTime, nullable=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")


RESOURCE_TYPES = [
    "clinical_note",
    "prescription",
    "care_instruction",
    "clinical_file",
    "teleconsultation_meta",
    "exam_order",
    "exam_result",
    "exam_result_file",
    "appointment_meta",
    "audit_export",
    "consent_record",
]
