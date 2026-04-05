import uuid
import json
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_
from fastapi import HTTPException, status
from typing import Optional, List, Dict, Any

from app.models.step6_models import (
    AppointmentReview, AppointmentReviewVersion,
    ReviewVisibility, ReviewStatus,
    ProfessionalReputationStats,
    SafetyReport, SafetyReportEvidence,
    ReportStatus, ReportCategory, ReportSeverity,
    ModerationCase, ModerationCaseEvent, ModerationCaseEventType,
    ModerationCaseStatus, ModerationCasePriority,
    AccountSanction, SanctionType, SanctionStatus,
    TrustEvent, TrustEventCode
)
from app.models.step2_models import Appointment, AppointmentStatus
from app.models.step4_models import ConsultationStatus
from app.models.user import User
from app.models.person import Person
from app.schemas.step6_schemas import (
    ReviewCreate, ReviewPatientProfessionalCreate, ReviewProfessionalPatientCreate,
    SafetyReportCreate, ModerationCaseCreate, SanctionCreate,
    ModerationCaseAddNote, PreventiveSuspensionCreate, SanctionLift,
    ReportResolve
)


class ModerationAuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_moderation_action(
        self,
        action: str,
        actor_user_id: str,
        resource_type: str,
        resource_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        from app.models.audit import AuditEvent, Severity
        event = AuditEvent(
            id=str(uuid.uuid4()),
            user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            severity=Severity.INFO,
            metadata_json=json.dumps(metadata) if metadata else None,
            ip_address=None,
            user_agent=None,
            created_at=datetime.utcnow()
        )
        self.db.add(event)
        await self.db.flush()
        return event

    async def log_case_event(
        self,
        case_id: str,
        event_type: str,
        actor_user_id: str,
        payload: Optional[Dict[str, Any]] = None
    ):
        event = ModerationCaseEvent(
            id=str(uuid.uuid4()),
            moderation_case_id=case_id,
            event_type=event_type,
            event_payload_json=json.dumps(payload) if payload else None,
            created_by_user_id=actor_user_id,
            created_at=datetime.utcnow()
        )
        self.db.add(event)
        await self.db.flush()
        return event


class SanctionEnforcementService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def is_target_restricted(
        self,
        target_type: str,
        target_id: str,
        action_code: str
    ) -> bool:
        result = await self.db.execute(
            select(AccountSanction).where(
                AccountSanction.target_type == target_type,
                AccountSanction.target_id == target_id,
                AccountSanction.status == SanctionStatus.ACTIVE,
                AccountSanction.deleted_at.is_(None)
            )
        )
        sanctions = result.scalars().all()
        if not sanctions:
            return False

        now = datetime.utcnow()
        for s in sanctions:
            if s.starts_at > now:
                continue
            if s.ends_at and s.ends_at < now:
                continue

            if s.sanction_type in [SanctionType.TEMPORARY_SUSPENSION, SanctionType.PERMANENT_SUSPENSION]:
                if action_code in ["professional_public_visibility", "professional_can_receive_booking",
                                   "patient_can_book", "laboratory_public_visibility",
                                   "laboratory_can_accept_order"]:
                    return True
            elif s.sanction_type == SanctionType.VISIBILITY_RESTRICTION:
                if action_code in ["professional_public_visibility", "laboratory_public_visibility"]:
                    return True

        return False

    async def get_active_sanctions(
        self,
        target_type: str,
        target_id: str
    ) -> List[AccountSanction]:
        result = await self.db.execute(
            select(AccountSanction).where(
                AccountSanction.target_type == target_type,
                AccountSanction.target_id == target_id,
                AccountSanction.status == SanctionStatus.ACTIVE,
                AccountSanction.deleted_at.is_(None)
            )
        )
        now = datetime.utcnow()
        active = []
        for s in result.scalars().all():
            if s.starts_at <= now and (s.ends_at is None or s.ends_at >= now):
                active.append(s)
        return active


class ReputationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def recalculate_reputation(self, professional_id: str):
        result = await self.db.execute(
            select(AppointmentReview).where(
                AppointmentReview.target_user_id == professional_id,
                AppointmentReview.target_role_code == "professional",
                AppointmentReview.visibility == ReviewVisibility.PUBLIC,
                AppointmentReview.status == ReviewStatus.PUBLISHED,
                AppointmentReview.deleted_at.is_(None)
            )
        )
        reviews = result.scalars().all()
        count = len(reviews)
        hidden_count = 0

        if count == 0:
            avg_overall = avg_punct = avg_comm = avg_resp = Decimal("0")
        else:
            total_overall = sum(r.rating_overall for r in reviews)
            avg_overall = Decimal(str(total_overall / count)).quantize(Decimal("0.01"))

            puncts = [r.rating_punctuality for r in reviews if r.rating_punctuality]
            avg_punct = Decimal(str(sum(puncts) / len(puncts))).quantize(Decimal("0.01")) if puncts else Decimal("0")

            comms = [r.rating_communication for r in reviews if r.rating_communication]
            avg_comm = Decimal(str(sum(comms) / len(comms))).quantize(Decimal("0.01")) if comms else Decimal("0")

            resps = [r.rating_respect for r in reviews if r.rating_respect]
            avg_resp = Decimal(str(sum(resps) / len(resps))).quantize(Decimal("0.01")) if resps else Decimal("0")

        hidden_result = await self.db.execute(
            select(func.count(AppointmentReview.id)).where(
                AppointmentReview.target_user_id == professional_id,
                AppointmentReview.target_role_code == "professional",
                AppointmentReview.status == ReviewStatus.HIDDEN,
                AppointmentReview.deleted_at.is_(None)
            )
        )
        hidden_count = hidden_result.scalar() or 0

        stats_result = await self.db.execute(
            select(ProfessionalReputationStats).where(
                ProfessionalReputationStats.professional_id == professional_id
            )
        )
        stats = stats_result.scalar_one_or_none()

        if not stats:
            stats = ProfessionalReputationStats(
                id=str(uuid.uuid4()),
                professional_id=professional_id,
                public_reviews_count=count,
                avg_overall=avg_overall,
                avg_punctuality=avg_punct,
                avg_communication=avg_comm,
                avg_respect=avg_resp,
                hidden_reviews_count=hidden_count,
                last_calculated_at=datetime.utcnow(),
                version="1"
            )
            self.db.add(stats)
        else:
            stats.public_reviews_count = count
            stats.avg_overall = avg_overall
            stats.avg_punctuality = avg_punct
            stats.avg_communication = avg_comm
            stats.avg_respect = avg_resp
            stats.hidden_reviews_count = hidden_count
            stats.last_calculated_at = datetime.utcnow()
            stats.version = str(int(stats.version or "1") + 1)

        await self.db.flush()
        return stats

    async def get_reputation(self, professional_id: str) -> Optional[ProfessionalReputationStats]:
        result = await self.db.execute(
            select(ProfessionalReputationStats).where(
                ProfessionalReputationStats.professional_id == professional_id
            )
        )
        return result.scalar_one_or_none()


class ReviewService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_eligibility(self, patient_id: str, professional_id: str) -> List[Dict[str, Any]]:
        result = await self.db.execute(
            select(Appointment).where(
                Appointment.patient_id == patient_id,
                Appointment.professional_id == professional_id,
                Appointment.status == AppointmentStatus.COMPLETED,
                Appointment.deleted_at.is_(None)
            )
        )
        appointments = result.scalars().all()

        eligible = []
        for appt in appointments:
            reviewed_result = await self.db.execute(
                select(AppointmentReview).where(
                    AppointmentReview.appointment_id == appt.id,
                    AppointmentReview.reviewer_user_id == patient_id,
                    AppointmentReview.deleted_at.is_(None)
                )
            )
            existing = reviewed_result.scalar_one_or_none()

            can_review = existing is None
            reason = None
            if existing:
                reason = "Review already submitted"
            elif appt.status != AppointmentStatus.COMPLETED:
                can_review = False
                reason = "Appointment not completed"

            eligible.append({
                "appointment_id": appt.id,
                "can_review_professional": can_review,
                "reason": reason
            })

        return eligible

    async def create_patient_review(
        self,
        appointment_id: str,
        patient_id: str,
        professional_id: str,
        data: ReviewPatientProfessionalCreate
    ) -> AppointmentReview:
        appt_result = await self.db.execute(
            select(Appointment).where(Appointment.id == appointment_id)
        )
        appt = appt_result.scalar_one_or_none()
        if not appt or appt.deleted_at:
            raise HTTPException(status_code=404, detail="Appointment not found")
        if appt.status != AppointmentStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Only completed appointments can be reviewed")
        if str(appt.patient_id) != str(patient_id):
            raise HTTPException(status_code=403, detail="Not your appointment")
        if str(appt.professional_id) != str(professional_id):
            raise HTTPException(status_code=403, detail="Not the assigned professional")

        existing_result = await self.db.execute(
            select(AppointmentReview).where(
                AppointmentReview.appointment_id == appointment_id,
                AppointmentReview.reviewer_user_id == patient_id,
                AppointmentReview.target_user_id == professional_id,
                AppointmentReview.deleted_at.is_(None)
            )
        )
        if existing_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Review already exists for this direction")

        review = AppointmentReview(
            id=str(uuid.uuid4()),
            appointment_id=appointment_id,
            reviewer_user_id=patient_id,
            reviewer_role_code="patient",
            target_user_id=professional_id,
            target_role_code="professional",
            rating_overall=data.rating_overall,
            rating_punctuality=data.rating_punctuality,
            rating_communication=data.rating_communication,
            rating_respect=data.rating_respect,
            comment_text=data.comment_text,
            visibility=ReviewVisibility.PUBLIC,
            status=ReviewStatus.PUBLISHED,
            moderation_flag=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version="1"
        )
        self.db.add(review)

        await self.db.execute(
            update(Appointment)
            .where(Appointment.id == appointment_id)
            .values(patient_review_submitted=True)
        )

        await self.db.flush()
        return review

    async def create_professional_review(
        self,
        appointment_id: str,
        professional_id: str,
        patient_id: str,
        data: ReviewProfessionalPatientCreate
    ) -> AppointmentReview:
        appt_result = await self.db.execute(
            select(Appointment).where(Appointment.id == appointment_id)
        )
        appt = appt_result.scalar_one_or_none()
        if not appt or appt.deleted_at:
            raise HTTPException(status_code=404, detail="Appointment not found")
        if appt.status != AppointmentStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Only completed appointments can be reviewed")
        if str(appt.professional_id) != str(professional_id):
            raise HTTPException(status_code=403, detail="Not your appointment")

        existing_result = await self.db.execute(
            select(AppointmentReview).where(
                AppointmentReview.appointment_id == appointment_id,
                AppointmentReview.reviewer_user_id == professional_id,
                AppointmentReview.target_user_id == patient_id,
                AppointmentReview.deleted_at.is_(None)
            )
        )
        if existing_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Review already exists for this direction")

        review = AppointmentReview(
            id=str(uuid.uuid4()),
            appointment_id=appointment_id,
            reviewer_user_id=professional_id,
            reviewer_role_code="professional",
            target_user_id=patient_id,
            target_role_code="patient",
            rating_overall=data.rating_overall,
            rating_respect=data.rating_respect,
            comment_text=data.comment_text,
            visibility=ReviewVisibility.INTERNAL_ONLY,
            status=ReviewStatus.PUBLISHED,
            moderation_flag=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version="1"
        )
        self.db.add(review)

        await self.db.execute(
            update(Appointment)
            .where(Appointment.id == appointment_id)
            .values(professional_review_submitted=True)
        )

        await self.db.flush()
        return review

    async def get_public_reviews(self, professional_id: str) -> List[AppointmentReview]:
        result = await self.db.execute(
            select(AppointmentReview).where(
                AppointmentReview.target_user_id == professional_id,
                AppointmentReview.target_role_code == "professional",
                AppointmentReview.visibility == ReviewVisibility.PUBLIC,
                AppointmentReview.status == ReviewStatus.PUBLISHED,
                AppointmentReview.deleted_at.is_(None)
            ).order_by(AppointmentReview.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_my_reviews(self, user_id: str) -> List[AppointmentReview]:
        result = await self.db.execute(
            select(AppointmentReview).where(
                AppointmentReview.reviewer_user_id == user_id,
                AppointmentReview.deleted_at.is_(None)
            ).order_by(AppointmentReview.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_review_by_id(self, review_id: str) -> Optional[AppointmentReview]:
        result = await self.db.execute(
            select(AppointmentReview).where(
                AppointmentReview.id == review_id,
                AppointmentReview.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def hide_review(self, review_id: str, admin_id: str) -> AppointmentReview:
        review = await self.get_review_by_id(review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")

        version_record = AppointmentReviewVersion(
            id=str(uuid.uuid4()),
            review_id=review.id,
            version_number=1,
            snapshot_json=json.dumps({
                "status": review.status,
                "rating_overall": review.rating_overall,
                "comment_text": review.comment_text,
                "version": review.version
            }),
            changed_by_user_id=admin_id,
            change_reason="Hidden by moderation",
            created_at=datetime.utcnow()
        )
        self.db.add(version_record)

        review.status = ReviewStatus.HIDDEN
        review.updated_at = datetime.utcnow()
        review.version = str(int(review.version or "1") + 1)
        await self.db.flush()
        return review

    async def restore_review(self, review_id: str, admin_id: str) -> AppointmentReview:
        review = await self.get_review_by_id(review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")

        review.status = ReviewStatus.PUBLISHED
        review.updated_at = datetime.utcnow()
        review.version = str(int(review.version or "1") + 1)
        await self.db.flush()
        return review


class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_report(
        self,
        reporter_user_id: str,
        data: SafetyReportCreate
    ) -> SafetyReport:
        report = SafetyReport(
            id=str(uuid.uuid4()),
            reporter_user_id=reporter_user_id,
            subject_type=data.subject_type,
            subject_id=data.subject_id,
            appointment_id=data.appointment_id,
            category_code=data.category_code,
            severity_claimed=data.severity_claimed,
            description=data.description,
            is_counterparty_hidden=True,
            status=ReportStatus.SUBMITTED,
            submitted_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version="1"
        )
        self.db.add(report)

        if data.evidence_files:
            for file_id in data.evidence_files:
                evidence = SafetyReportEvidence(
                    id=str(uuid.uuid4()),
                    report_id=report.id,
                    file_id=file_id,
                    evidence_type="other",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    version="1"
                )
                self.db.add(evidence)

        await self.db.flush()
        return report

    async def get_report(self, report_id: str) -> Optional[SafetyReport]:
        result = await self.db.execute(
            select(SafetyReport).where(
                SafetyReport.id == report_id,
                SafetyReport.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def get_reports_by_reporter(self, reporter_id: str) -> List[SafetyReport]:
        result = await self.db.execute(
            select(SafetyReport).where(
                SafetyReport.reporter_user_id == reporter_id,
                SafetyReport.deleted_at.is_(None)
            ).order_by(SafetyReport.submitted_at.desc())
        )
        return list(result.scalars().all())

    async def assign_report(self, report_id: str, admin_id: str) -> SafetyReport:
        report = await self.get_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        report.assigned_admin_id = admin_id
        report.status = ReportStatus.UNDER_REVIEW
        report.updated_at = datetime.utcnow()
        report.version = str(int(report.version or "1") + 1)
        await self.db.flush()
        return report

    async def resolve_report(self, report_id: str, summary: str) -> SafetyReport:
        report = await self.get_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        report.status = ReportStatus.RESOLVED
        report.resolution_summary = summary
        report.resolved_at = datetime.utcnow()
        report.updated_at = datetime.utcnow()
        report.version = str(int(report.version or "1") + 1)
        await self.db.flush()
        return report

    async def reject_report(self, report_id: str, summary: str) -> SafetyReport:
        report = await self.get_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        report.status = ReportStatus.REJECTED
        report.resolution_summary = summary
        report.resolved_at = datetime.utcnow()
        report.updated_at = datetime.utcnow()
        report.version = str(int(report.version or "1") + 1)
        await self.db.flush()
        return report

    async def list_reports(
        self,
        status_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[SafetyReport]:
        query = select(SafetyReport).where(SafetyReport.deleted_at.is_(None))
        if status_filter:
            query = query.where(SafetyReport.status == status_filter)
        query = query.order_by(SafetyReport.submitted_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())


class ModerationCaseService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_case(
        self,
        source_type: str,
        target_type: str,
        target_id: str,
        priority: str,
        source_id: Optional[str] = None,
        admin_id: Optional[str] = None
    ) -> ModerationCase:
        case = ModerationCase(
            id=str(uuid.uuid4()),
            source_type=source_type,
            source_id=source_id,
            target_type=target_type,
            target_id=target_id,
            status=ModerationCaseStatus.OPEN,
            priority=priority,
            assigned_admin_id=admin_id,
            opened_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version="1"
        )
        self.db.add(case)
        await self.db.flush()
        return case

    async def get_case(self, case_id: str) -> Optional[ModerationCase]:
        result = await self.db.execute(
            select(ModerationCase).where(
                ModerationCase.id == case_id,
                ModerationCase.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def add_note(
        self,
        case_id: str,
        note: str,
        admin_id: str
    ) -> ModerationCaseEvent:
        event = ModerationCaseEvent(
            id=str(uuid.uuid4()),
            moderation_case_id=case_id,
            event_type=ModerationCaseEventType.NOTE_ADDED,
            event_payload_json=json.dumps({"note": note}),
            created_by_user_id=admin_id,
            created_at=datetime.utcnow()
        )
        self.db.add(event)
        await self.db.flush()
        return event

    async def assign_case(self, case_id: str, admin_id: str) -> ModerationCase:
        case = await self.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        case.assigned_admin_id = admin_id
        case.status = ModerationCaseStatus.UNDER_REVIEW
        case.updated_at = datetime.utcnow()
        case.version = str(int(case.version or "1") + 1)
        await self.db.flush()
        return case

    async def apply_preventive_suspension(
        self,
        case_id: str,
        admin_id: str,
        target_type: str,
        target_id: str,
        sanction_type: str,
        reason_code: str,
        reason_text: Optional[str],
        starts_at: datetime,
        ends_at: Optional[datetime]
    ) -> AccountSanction:
        sanction_service = SanctionEnforcementService(self.db)
        sanction = AccountSanction(
            id=str(uuid.uuid4()),
            target_type=target_type,
            target_id=target_id,
            sanction_type=sanction_type,
            reason_code=reason_code,
            reason_text=reason_text,
            starts_at=starts_at,
            ends_at=ends_at,
            status=SanctionStatus.ACTIVE,
            applied_by_user_id=admin_id,
            moderation_case_id=case_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version="1"
        )
        self.db.add(sanction)

        case = await self.get_case(case_id)
        if case:
            case.status = ModerationCaseStatus.PREVENTIVE_ACTION
            case.updated_at = datetime.utcnow()
            case.version = str(int(case.version or "1") + 1)

        await self.db.flush()
        return sanction

    async def resolve_case(
        self,
        case_id: str,
        outcome_code: str,
        outcome_summary: str,
        admin_id: str
    ) -> ModerationCase:
        case = await self.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        case.status = ModerationCaseStatus.RESOLVED
        case.outcome_code = outcome_code
        case.outcome_summary = outcome_summary
        case.closed_at = datetime.utcnow()
        case.updated_at = datetime.utcnow()
        case.version = str(int(case.version or "1") + 1)
        await self.db.flush()
        return case

    async def dismiss_case(
        self,
        case_id: str,
        outcome_summary: str,
        admin_id: str
    ) -> ModerationCase:
        case = await self.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        case.status = ModerationCaseStatus.DISMISSED
        case.outcome_summary = outcome_summary
        case.closed_at = datetime.utcnow()
        case.updated_at = datetime.utcnow()
        case.version = str(int(case.version or "1") + 1)
        await self.db.flush()
        return case

    async def list_cases(
        self,
        status_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ModerationCase]:
        query = select(ModerationCase).where(ModerationCase.deleted_at.is_(None))
        if status_filter:
            query = query.where(ModerationCase.status == status_filter)
        query = query.order_by(ModerationCase.opened_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_case_events(self, case_id: str) -> List[ModerationCaseEvent]:
        result = await self.db.execute(
            select(ModerationCaseEvent).where(
                ModerationCaseEvent.moderation_case_id == case_id
            ).order_by(ModerationCaseEvent.created_at.asc())
        )
        return list(result.scalars().all())


class SanctionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_sanction(
        self,
        target_type: str,
        target_id: str,
        sanction_type: str,
        reason_code: str,
        reason_text: Optional[str],
        starts_at: datetime,
        ends_at: Optional[datetime],
        applied_by_user_id: str,
        moderation_case_id: Optional[str] = None
    ) -> AccountSanction:
        if sanction_type == SanctionType.TEMPORARY_SUSPENSION and not ends_at:
            raise HTTPException(status_code=400, detail="Temporary suspension requires ends_at")

        sanction = AccountSanction(
            id=str(uuid.uuid4()),
            target_type=target_type,
            target_id=target_id,
            sanction_type=sanction_type,
            reason_code=reason_code,
            reason_text=reason_text,
            starts_at=starts_at,
            ends_at=ends_at,
            status=SanctionStatus.ACTIVE,
            applied_by_user_id=applied_by_user_id,
            moderation_case_id=moderation_case_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version="1"
        )
        self.db.add(sanction)
        await self.db.flush()
        return sanction

    async def get_sanction(self, sanction_id: str) -> Optional[AccountSanction]:
        result = await self.db.execute(
            select(AccountSanction).where(
                AccountSanction.id == sanction_id,
                AccountSanction.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def lift_sanction(
        self,
        sanction_id: str,
        lifted_by_user_id: str,
        reason: str
    ) -> AccountSanction:
        sanction = await self.get_sanction(sanction_id)
        if not sanction:
            raise HTTPException(status_code=404, detail="Sanction not found")
        if sanction.status != SanctionStatus.ACTIVE:
            raise HTTPException(status_code=400, detail="Sanction is not active")

        sanction.status = SanctionStatus.LIFTED
        sanction.lifted_by_user_id = lifted_by_user_id
        sanction.lifted_reason = reason
        sanction.updated_at = datetime.utcnow()
        sanction.version = str(int(sanction.version or "1") + 1)
        await self.db.flush()
        return sanction

    async def list_sanctions(
        self,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[AccountSanction]:
        query = select(AccountSanction).where(AccountSanction.deleted_at.is_(None))
        if target_type:
            query = query.where(AccountSanction.target_type == target_type)
        if target_id:
            query = query.where(AccountSanction.target_id == target_id)
        if status_filter:
            query = query.where(AccountSanction.status == status_filter)
        query = query.order_by(AccountSanction.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())


class TrustEventService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_event(
        self,
        target_type: str,
        target_id: str,
        event_code: str,
        weight: int = 0,
        metadata: Optional[Dict] = None
    ):
        event = TrustEvent(
            id=str(uuid.uuid4()),
            target_type=target_type,
            target_id=target_id,
            event_code=event_code,
            weight=weight,
            metadata_json=json.dumps(metadata) if metadata else None,
            created_at=datetime.utcnow()
        )
        self.db.add(event)
        await self.db.flush()
        return event
