from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class DataClassificationResponse(BaseModel):
    id: str
    code: str
    name: str
    description: Optional[str] = None
    severity_level: int


class ResourceAccessPolicyUpdate(BaseModel):
    classification_code: str
    access_mode: str
    requires_relationship: bool = True
    requires_patient_authorization: bool = False
    requires_justification: bool = False
    max_access_minutes: Optional[int] = None
    allow_download: bool = False


class ResourceAccessPolicyResponse(BaseModel):
    resource_type: str
    classification_code: str
    access_mode: str
    requires_relationship: bool
    requires_patient_authorization: bool
    requires_justification: bool
    max_access_minutes: Optional[int] = None
    allow_download: bool
    is_active: bool


class ConsentCreate(BaseModel):
    consent_type: str
    source: str
    evidence_file_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None


class ConsentResponse(BaseModel):
    id: str
    patient_id: str
    consent_type: str
    status: str
    granted_at: datetime
    revoked_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    source: str
    evidence_file_id: Optional[str] = None
    granted_by_user_id: Optional[str] = None
    notes: Optional[str] = None


class ExceptionalAccessRequestCreate(BaseModel):
    patient_id: Optional[str] = None
    target_user_id: Optional[str] = None
    resource_type: str
    resource_id: Optional[str] = None
    scope_type: str
    justification: str
    business_basis: Optional[str] = None
    requested_minutes: int


class ExceptionalAccessRequestResponse(BaseModel):
    id: str
    requester_user_id: str
    requester_role_code: str
    patient_id: Optional[str] = None
    target_user_id: Optional[str] = None
    resource_type: str
    resource_id: Optional[str] = None
    scope_type: str
    justification: str
    business_basis: Optional[str] = None
    requested_minutes: int
    status: str
    requires_patient_authorization: bool
    patient_consent_id: Optional[str] = None
    approved_by_user_id: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_by_user_id: Optional[str] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    revoked_by_user_id: Optional[str] = None
    revoked_at: Optional[datetime] = None
    revoke_reason: Optional[str] = None
    created_at: datetime


class ApproveAccessRequest(BaseModel):
    starts_at: Optional[datetime] = None
    expires_at: datetime
    approval_note: Optional[str] = None


class RejectAccessRequest(BaseModel):
    reason: str


class RevokeAccessRequest(BaseModel):
    reason: str


class ClinicalAccessLogResponse(BaseModel):
    id: str
    actor_user_id: str
    actor_role_code: str
    patient_id: Optional[str] = None
    target_user_id: Optional[str] = None
    resource_type: str
    resource_id: Optional[str] = None
    access_mode: str
    action: str
    decision: str
    exceptional_access_request_id: Optional[str] = None
    justification: Optional[str] = None
    created_at: datetime


class ClinicalAccessLogExportResponse(BaseModel):
    id: str
    actor_user_id: str
    actor_role_code: str
    patient_id: Optional[str] = None
    target_user_id: Optional[str] = None
    resource_type: str
    resource_id: Optional[str] = None
    access_mode: str
    action: str
    decision: str
    exceptional_access_request_id: Optional[str] = None
    created_at: datetime


class ProcessingActivityCreate(BaseModel):
    code: str
    module_name: str
    purpose: str
    data_categories: List[str]
    subject_categories: List[str]
    legal_basis: Optional[str] = None
    retention_policy_id: Optional[str] = None
    is_sensitive: bool = True


class ProcessingActivityResponse(BaseModel):
    id: str
    code: str
    module_name: str
    purpose: str
    data_categories_json: str
    subject_categories_json: str
    legal_basis: Optional[str] = None
    retention_policy_id: Optional[str] = None
    is_sensitive: bool
    is_active: bool


class RetentionPolicyCreate(BaseModel):
    code: str
    resource_type: str
    retention_days: Optional[int] = None
    archive_after_days: Optional[int] = None
    delete_mode: str
    description: Optional[str] = None


class RetentionPolicyResponse(BaseModel):
    id: str
    code: str
    resource_type: str
    retention_days: Optional[int] = None
    archive_after_days: Optional[int] = None
    delete_mode: str
    description: Optional[str] = None
    is_active: bool


class PrivacyIncidentCreate(BaseModel):
    incident_type: str
    severity: str
    description: str
    affected_resource_type: Optional[str] = None
    affected_resource_id: Optional[str] = None


class PrivacyIncidentResponse(BaseModel):
    id: str
    incident_code: str
    detected_at: datetime
    reported_by_user_id: Optional[str] = None
    severity: str
    incident_type: str
    description: str
    affected_resource_type: Optional[str] = None
    affected_resource_id: Optional[str] = None
    status: str
    assigned_admin_id: Optional[str] = None
    resolution_summary: Optional[str] = None
    resolved_at: Optional[datetime] = None


class PrivacyIncidentAssign(BaseModel):
    admin_id: str


class PrivacyIncidentResolve(BaseModel):
    summary: str


class PrivacyIncidentContain(BaseModel):
    note: str


class PrivacyIncidentDismiss(BaseModel):
    summary: str


class PrivacyPolicyVersionCreate(BaseModel):
    policy_type: str
    version_code: str
    content_markdown: str


class PrivacyPolicyVersionResponse(BaseModel):
    id: str
    policy_type: str
    version_code: str
    content_markdown: str
    is_active: bool
    published_at: Optional[datetime] = None
    created_at: datetime


class EvaluateAccessResponse(BaseModel):
    allowed: bool
    mode: str
    decision_reason: str
    policy_snapshot: Optional[dict] = None
    requires_exceptional_request: bool


class ApproveAccessResponse(BaseModel):
    request_id: str
    status: str
    grant_id: str
    granted_until: datetime


class ExceptionalAccessGrantResponse(BaseModel):
    id: str
    request_id: str
    grantee_user_id: str
    resource_type: str
    resource_id: Optional[str] = None
    scope_type: str
    granted_at: datetime
    expires_at: datetime
    status: str


class PrivacyIncidentEventResponse(BaseModel):
    id: str
    privacy_incident_id: str
    event_type: str
    event_payload_json: Optional[str] = None
    created_by_user_id: str
    created_at: datetime
