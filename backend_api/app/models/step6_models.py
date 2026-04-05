import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, SmallInteger, Numeric, Text
from app.core.database import Base


class ReviewVisibility:
    PUBLIC = "public"
    INTERNAL_ONLY = "internal_only"


class ReviewStatus:
    PUBLISHED = "published"
    HIDDEN = "hidden"
    WITHDRAWN = "withdrawn"


class AppointmentReview(Base):
    __tablename__ = "appointment_reviews"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    appointment_id = Column(String, nullable=False, index=True)
    reviewer_user_id = Column(String, nullable=False, index=True)
    reviewer_role_code = Column(String, nullable=False)
    target_user_id = Column(String, nullable=False, index=True)
    target_role_code = Column(String, nullable=False)
    rating_overall = Column(SmallInteger, nullable=False)
    rating_punctuality = Column(SmallInteger, nullable=True)
    rating_communication = Column(SmallInteger, nullable=True)
    rating_respect = Column(SmallInteger, nullable=True)
    comment_text = Column(Text, nullable=True)
    visibility = Column(String, nullable=False)
    status = Column(String, nullable=False)
    moderation_flag = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")


class AppointmentReviewVersion(Base):
    __tablename__ = "appointment_review_versions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    review_id = Column(String, nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    snapshot_json = Column(Text, nullable=False)
    changed_by_user_id = Column(String, nullable=False)
    change_reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ProfessionalReputationStats(Base):
    __tablename__ = "professional_reputation_stats"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    professional_id = Column(String, unique=True, nullable=False)
    public_reviews_count = Column(Integer, default=0)
    avg_overall = Column(Numeric(4, 2), default=0)
    avg_punctuality = Column(Numeric(4, 2), default=0)
    avg_communication = Column(Numeric(4, 2), default=0)
    avg_respect = Column(Numeric(4, 2), default=0)
    hidden_reviews_count = Column(Integer, default=0)
    last_calculated_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")


class ReportCategory:
    ABUSE = "abuse"
    FRAUD = "fraud"
    HARASSMENT = "harassment"
    IMPERSONATION = "impersonation"
    NO_SHOW = "no_show"
    UNSAFE_BEHAVIOR = "unsafe_behavior"
    FAKE_PROFILE = "fake_profile"
    INAPPROPRIATE_REVIEW = "inappropriate_review"
    OTHER = "other"


class ReportSeverity:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReportStatus:
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    ACTION_REQUIRED = "action_required"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class SafetyReport(Base):
    __tablename__ = "safety_reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    reporter_user_id = Column(String, nullable=False, index=True)
    subject_type = Column(String, nullable=False)
    subject_id = Column(String, nullable=False, index=True)
    appointment_id = Column(String, nullable=True, index=True)
    category_code = Column(String, nullable=False)
    severity_claimed = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    is_counterparty_hidden = Column(Boolean, default=True)
    status = Column(String, nullable=False)
    submitted_at = Column(DateTime, nullable=False)
    assigned_admin_id = Column(String, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")


class SafetyReportEvidence(Base):
    __tablename__ = "safety_report_evidences"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String, nullable=False, index=True)
    file_id = Column(String, nullable=False)
    evidence_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")


class ModerationCaseStatus:
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    PREVENTIVE_ACTION = "preventive_action"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ModerationCasePriority:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ModerationCase(Base):
    __tablename__ = "moderation_cases"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_type = Column(String, nullable=False)
    source_id = Column(String, nullable=True)
    target_type = Column(String, nullable=False)
    target_id = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False)
    priority = Column(String, nullable=False)
    assigned_admin_id = Column(String, nullable=True)
    opened_at = Column(DateTime, nullable=False)
    closed_at = Column(DateTime, nullable=True)
    outcome_code = Column(String, nullable=True)
    outcome_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")


class ModerationCaseEventType:
    OPENED = "opened"
    ASSIGNED = "assigned"
    NOTE_ADDED = "note_added"
    PREVENTIVE_SUSPENSION = "preventive_suspension"
    REVIEW_HIDDEN = "review_hidden"
    SANCTION_APPLIED = "sanction_applied"
    SANCTION_LIFTED = "sanction_lifted"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ModerationCaseEvent(Base):
    __tablename__ = "moderation_case_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    moderation_case_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    event_payload_json = Column(Text, nullable=True)
    created_by_user_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class SanctionType:
    WARNING = "warning"
    TEMPORARY_SUSPENSION = "temporary_suspension"
    PERMANENT_SUSPENSION = "permanent_suspension"
    VISIBILITY_RESTRICTION = "visibility_restriction"
    REVIEW_HIDDEN = "review_hidden"


class SanctionStatus:
    ACTIVE = "active"
    LIFTED = "lifted"
    EXPIRED = "expired"


class AccountSanction(Base):
    __tablename__ = "account_sanctions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    target_type = Column(String, nullable=False)
    target_id = Column(String, nullable=False, index=True)
    sanction_type = Column(String, nullable=False)
    reason_code = Column(String, nullable=False)
    reason_text = Column(Text, nullable=True)
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False)
    applied_by_user_id = Column(String, nullable=False)
    lifted_by_user_id = Column(String, nullable=True)
    lifted_reason = Column(Text, nullable=True)
    moderation_case_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")


class TrustEventCode:
    COMPLETED_REVIEW = "completed_review"
    REPORT_CREATED = "report_created"
    REPORT_RESOLVED = "report_resolved"
    SANCTION_APPLIED = "sanction_applied"
    SANCTION_LIFTED = "sanction_lifted"


class TrustEvent(Base):
    __tablename__ = "trust_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    target_type = Column(String, nullable=False)
    target_id = Column(String, nullable=False, index=True)
    event_code = Column(String, nullable=False)
    weight = Column(Integer, default=0)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
