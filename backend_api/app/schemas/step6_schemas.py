from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ReviewCreate(BaseModel):
    rating_overall: int = Field(..., ge=1, le=5)
    rating_punctuality: Optional[int] = Field(None, ge=1, le=5)
    rating_communication: Optional[int] = Field(None, ge=1, le=5)
    rating_respect: Optional[int] = Field(None, ge=1, le=5)
    comment_text: Optional[str] = None


class ReviewPatientProfessionalCreate(ReviewCreate):
    pass


class ReviewProfessionalPatientCreate(BaseModel):
    rating_overall: int = Field(..., ge=1, le=5)
    rating_respect: Optional[int] = Field(None, ge=1, le=5)
    comment_text: Optional[str] = None


class ReviewResponse(BaseModel):
    id: str
    appointment_id: str
    reviewer_user_id: str
    reviewer_role_code: str
    target_user_id: str
    target_role_code: str
    rating_overall: int
    rating_punctuality: Optional[int] = None
    rating_communication: Optional[int] = None
    rating_respect: Optional[int] = None
    comment_text: Optional[str] = None
    visibility: str
    status: str
    created_at: datetime


class ReviewPublicResponse(BaseModel):
    id: str
    rating_overall: int
    rating_punctuality: Optional[int] = None
    rating_communication: Optional[int] = None
    rating_respect: Optional[int] = None
    comment_text: Optional[str] = None
    reviewer_name_abbrev: str
    created_at: datetime


class ReviewEligibilityResponse(BaseModel):
    appointment_id: str
    can_review_professional: bool
    reason: Optional[str] = None


class ReputationSummaryResponse(BaseModel):
    professional_id: str
    public_reviews_count: int
    avg_overall: float
    avg_punctuality: Optional[float] = None
    avg_communication: Optional[float] = None
    avg_respect: Optional[float] = None


class SafetyReportCreate(BaseModel):
    subject_type: str
    subject_id: str
    appointment_id: Optional[str] = None
    category_code: str
    severity_claimed: str
    description: str = Field(..., min_length=10)
    evidence_files: Optional[List[str]] = None


class SafetyReportResponse(BaseModel):
    id: str
    reporter_user_id: str
    subject_type: str
    subject_id: str
    appointment_id: Optional[str] = None
    category_code: str
    severity_claimed: str
    description: str
    is_counterparty_hidden: bool
    status: str
    submitted_at: datetime
    assigned_admin_id: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_summary: Optional[str] = None


class ModerationCaseCreate(BaseModel):
    source_type: str
    source_id: Optional[str] = None
    target_type: str
    target_id: str
    priority: str


class ModerationCaseResponse(BaseModel):
    id: str
    source_type: str
    source_id: Optional[str] = None
    target_type: str
    target_id: str
    status: str
    priority: str
    assigned_admin_id: Optional[str] = None
    opened_at: datetime
    closed_at: Optional[datetime] = None
    outcome_code: Optional[str] = None
    outcome_summary: Optional[str] = None


class ModerationCaseEventResponse(BaseModel):
    id: str
    moderation_case_id: str
    event_type: str
    event_payload_json: Optional[str] = None
    created_by_user_id: str
    created_at: datetime


class ModerationCaseAddNote(BaseModel):
    note: str


class PreventiveSuspensionCreate(BaseModel):
    target_type: str
    target_id: str
    sanction_type: str
    reason_code: str
    reason_text: Optional[str] = None
    starts_at: datetime
    ends_at: Optional[datetime] = None


class SanctionCreate(BaseModel):
    target_type: str
    target_id: str
    sanction_type: str
    reason_code: str
    reason_text: Optional[str] = None
    starts_at: datetime
    ends_at: Optional[datetime] = None
    moderation_case_id: Optional[str] = None


class SanctionResponse(BaseModel):
    id: str
    target_type: str
    target_id: str
    sanction_type: str
    reason_code: str
    reason_text: Optional[str] = None
    starts_at: datetime
    ends_at: Optional[datetime] = None
    status: str
    applied_by_user_id: str
    lifted_by_user_id: Optional[str] = None
    lifted_reason: Optional[str] = None
    moderation_case_id: Optional[str] = None


class SanctionLift(BaseModel):
    reason: str


class ReportAssign(BaseModel):
    admin_id: str


class ReportResolve(BaseModel):
    summary: str


class ReviewHideRestore(BaseModel):
    reason: Optional[str] = None


class ReviewListResponse(BaseModel):
    id: str
    appointment_id: str
    reviewer_user_id: str
    reviewer_role_code: str
    target_user_id: str
    target_role_code: str
    rating_overall: int
    rating_punctuality: Optional[int] = None
    rating_communication: Optional[int] = None
    rating_respect: Optional[int] = None
    comment_text: Optional[str] = None
    visibility: str
    status: str
    moderation_flag: bool
    created_at: datetime
