from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.moderation_authorization import require_admin_moderation
from app.models.user import User
from app.models.step6_models import ModerationCaseEventType
from app.services.step6_services import (
    ReportService, ModerationCaseService, ReviewService,
    SanctionService, ReputationService, ModerationAuditService
)
from app.schemas.step6_schemas import (
    SafetyReportResponse, ModerationCaseResponse, ModerationCaseCreate,
    ModerationCaseEventResponse, ModerationCaseAddNote, PreventiveSuspensionCreate,
    SanctionResponse, SanctionCreate, SanctionLift, ReportAssign, ReportResolve,
    ReviewListResponse, ReviewHideRestore
)

router = APIRouter()


# REPORTS
@router.get("/reports", response_model=List[SafetyReportResponse])
async def list_reports(
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    current_user: User = Depends(require_admin_moderation),
    db: AsyncSession = Depends(get_db)
):
    service = ReportService(db)
    audit_service = ModerationAuditService(db)

    await audit_service.log_moderation_action(
        action="reports_listed",
        actor_user_id=str(current_user.id),
        resource_type="safety_report",
        resource_id="list"
    )
    await db.commit()

    reports = await service.list_reports(status_filter=status, limit=limit, offset=offset)
    return [
        SafetyReportResponse(
            id=r.id, reporter_user_id=r.reporter_user_id,
            subject_type=r.subject_type, subject_id=r.subject_id,
            appointment_id=r.appointment_id,
            category_code=r.category_code, severity_claimed=r.severity_claimed,
            description=r.description, is_counterparty_hidden=r.is_counterparty_hidden,
            status=r.status, submitted_at=r.submitted_at,
            assigned_admin_id=r.assigned_admin_id,
            resolved_at=r.resolved_at, resolution_summary=r.resolution_summary
        )
        for r in reports
    ]


@router.get("/reports/{report_id}", response_model=SafetyReportResponse)
async def get_report(
    report_id: str,
    current_user: User = Depends(require_admin_moderation),
    db: AsyncSession = Depends(get_db)
):
    service = ReportService(db)
    audit_service = ModerationAuditService(db)

    report = await service.get_report(report_id)
    if not report:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=404, detail="Report not found")

    await audit_service.log_moderation_action(
        action="report_viewed",
        actor_user_id=str(current_user.id),
        resource_type="safety_report",
        resource_id=report_id
    )
    await db.commit()

    return SafetyReportResponse(
        id=report.id, reporter_user_id=report.reporter_user_id,
        subject_type=report.subject_type, subject_id=report.subject_id,
        appointment_id=report.appointment_id,
        category_code=report.category_code, severity_claimed=report.severity_claimed,
        description=report.description, is_counterparty_hidden=report.is_counterparty_hidden,
        status=report.status, submitted_at=report.submitted_at,
        assigned_admin_id=report.assigned_admin_id,
        resolved_at=report.resolved_at, resolution_summary=report.resolution_summary
    )


@router.post("/reports/{report_id}/assign")
async def assign_report(
    report_id: str,
    data: ReportAssign,
    current_user: User = Depends(require_admin_moderation),
    db: AsyncSession = Depends(get_db)
):
    service = ReportService(db)
    audit_service = ModerationAuditService(db)

    report = await service.assign_report(report_id, str(current_user.id))

    await audit_service.log_moderation_action(
        action="report_assigned",
        actor_user_id=str(current_user.id),
        resource_type="safety_report",
        resource_id=report_id,
        metadata={"assigned_admin_id": data.admin_id}
    )

    await audit_service.log_case_event(
        case_id=None,
        event_type="report_assigned",
        actor_user_id=str(current_user.id),
        payload={"report_id": report_id, "admin_id": data.admin_id}
    )

    await db.commit()
    return {"status": report.status, "assigned_admin_id": report.assigned_admin_id}


@router.post("/reports/{report_id}/mark-under-review")
async def mark_under_review(
    report_id: str,
    current_user: User = Depends(require_admin_moderation),
    db: AsyncSession = Depends(get_db)
):
    service = ReportService(db)
    audit_service = ModerationAuditService(db)

    report = await service.assign_report(report_id, str(current_user.id))

    await audit_service.log_moderation_action(
        action="report_under_review",
        actor_user_id=str(current_user.id),
        resource_type="safety_report",
        resource_id=report_id
    )
    await db.commit()
    return {"status": report.status}


@router.post("/reports/{report_id}/resolve")
async def resolve_report(
    report_id: str,
    data: ReportResolve,
    current_user: User = Depends(require_admin_moderation),
    db: AsyncSession = Depends(get_db)
):
    service = ReportService(db)
    audit_service = ModerationAuditService(db)

    report = await service.resolve_report(report_id, data.summary)

    await audit_service.log_moderation_action(
        action="report_resolved",
        actor_user_id=str(current_user.id),
        resource_type="safety_report",
        resource_id=report_id,
        metadata={"resolution_summary": data.summary}
    )
    await db.commit()
    return {"status": report.status, "resolved_at": report.resolved_at}


@router.post("/reports/{report_id}/reject")
async def reject_report(
    report_id: str,
    data: ReportResolve,
    current_user: User = Depends(require_admin_moderation),
    db: AsyncSession = Depends(get_db)
):
    service = ReportService(db)
    audit_service = ModerationAuditService(db)

    report = await service.reject_report(report_id, data.summary)

    await audit_service.log_moderation_action(
        action="report_rejected",
        actor_user_id=str(current_user.id),
        resource_type="safety_report",
        resource_id=report_id,
        metadata={"resolution_summary": data.summary}
    )
    await db.commit()
    return {"status": report.status, "resolved_at": report.resolved_at}


# CASES
@router.get("/cases", response_model=List[ModerationCaseResponse])
async def list_cases(
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    current_user: User = Depends(require_admin_moderation),
    db: AsyncSession = Depends(get_db)
):
    service = ModerationCaseService(db)
    audit_service = ModerationAuditService(db)

    await audit_service.log_moderation_action(
        action="cases_listed",
        actor_user_id=str(current_user.id),
        resource_type="moderation_case",
        resource_id="list"
    )
    await db.commit()

    cases = await service.list_cases(status_filter=status, limit=limit, offset=offset)
    return [
        ModerationCaseResponse(
            id=c.id, source_type=c.source_type, source_id=c.source_id,
            target_type=c.target_type, target_id=c.target_id,
            status=c.status, priority=c.priority,
            assigned_admin_id=c.assigned_admin_id,
            opened_at=c.opened_at, closed_at=c.closed_at,
            outcome_code=c.outcome_code, outcome_summary=c.outcome_summary
        )
        for c in cases
    ]


@router.get("/cases/{case_id}", response_model=ModerationCaseResponse)
async def get_case(
    case_id: str,
    current_user: User = Depends(require_admin_moderation),
    db: AsyncSession = Depends(get_db)
):
    service = ModerationCaseService(db)
    audit_service = ModerationAuditService(db)

    case = await service.get_case(case_id)
    if not case:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=404, detail="Case not found")

    await audit_service.log_moderation_action(
        action="case_viewed",
        actor_user_id=str(current_user.id),
        resource_type="moderation_case",
        resource_id=case_id
    )
    await db.commit()

    return ModerationCaseResponse(
        id=case.id, source_type=case.source_type, source_id=case.source_id,
        target_type=case.target_type, target_id=case.target_id,
        status=case.status, priority=case.priority,
        assigned_admin_id=case.assigned_admin_id,
        opened_at=case.opened_at, closed_at=case.closed_at,
        outcome_code=case.outcome_code, outcome_summary=case.outcome_summary
    )


@router.post("/cases")
async def create_case(
    data: ModerationCaseCreate,
    current_user: User = Depends(require_admin_moderation),
    db: AsyncSession = Depends(get_db)
):
    service = ModerationCaseService(db)
    audit_service = ModerationAuditService(db)

    case = await service.create_case(
        source_type=data.source_type,
        target_type=data.target_type,
        target_id=data.target_id,
        priority=data.priority,
        source_id=data.source_id,
        admin_id=str(current_user.id)
    )

    await audit_service.log_moderation_action(
        action="case_created",
        actor_user_id=str(current_user.id),
        resource_type="moderation_case",
        resource_id=case.id,
        metadata={"target_type": data.target_type, "priority": data.priority}
    )

    await audit_service.log_case_event(
        case_id=case.id,
        event_type=ModerationCaseEventType.OPENED,
        actor_user_id=str(current_user.id),
        payload={"source_type": data.source_type, "target_type": data.target_type}
    )

    await db.commit()
    return {
        "id": case.id,
        "status": case.status,
        "priority": case.priority,
        "opened_at": case.opened_at
    }


@router.post("/cases/{case_id}/add-note")
async def add_note(
    case_id: str,
    data: ModerationCaseAddNote,
    current_user: User = Depends(require_admin_moderation),
    db: AsyncSession = Depends(get_db)
):
    service = ModerationCaseService(db)
    audit_service = ModerationAuditService(db)

    event = await service.add_note(case_id, data.note, str(current_user.id))

    await audit_service.log_moderation_action(
        action="case_note_added",
        actor_user_id=str(current_user.id),
        resource_type="moderation_case",
        resource_id=case_id,
        metadata={"note": data.note}
    )

    await audit_service.log_case_event(
        case_id=case_id,
        event_type=ModerationCaseEventType.NOTE_ADDED,
        actor_user_id=str(current_user.id),
        payload={"note": data.note}
    )

    await db.commit()
    return {"event_id": event.id}


@router.post("/cases/{case_id}/apply-preventive-suspension")
async def apply_preventive_suspension(
    case_id: str,
    data: PreventiveSuspensionCreate,
    current_user: User = Depends(require_admin_moderation),
    db: AsyncSession = Depends(get_db)
):
    case_service = ModerationCaseService(db)
    sanction_service = SanctionService(db)
    audit_service = ModerationAuditService(db)

    sanction = await case_service.apply_preventive_suspension(
        case_id=case_id,
        admin_id=str(current_user.id),
        target_type=data.target_type,
        target_id=data.target_id,
        sanction_type=data.sanction_type,
        reason_code=data.reason_code,
        reason_text=data.reason_text,
        starts_at=data.starts_at,
        ends_at=data.ends_at
    )

    await audit_service.log_moderation_action(
        action="preventive_suspension_applied",
        actor_user_id=str(current_user.id),
        resource_type="account_sanction",
        resource_id=sanction.id,
        metadata={"case_id": case_id, "target_type": data.target_type}
    )

    await audit_service.log_case_event(
        case_id=case_id,
        event_type=ModerationCaseEventType.PREVENTIVE_SUSPENSION,
        actor_user_id=str(current_user.id),
        payload={"sanction_id": sanction.id, "sanction_type": data.sanction_type}
    )

    await db.commit()
    return {"sanction_id": sanction.id, "status": sanction.status}


@router.post("/cases/{case_id}/resolve")
async def resolve_case(
    case_id: str,
    outcome_code: str,
    outcome_summary: str,
    current_user: User = Depends(require_admin_moderation),
    db: AsyncSession = Depends(get_db)
):
    service = ModerationCaseService(db)
    audit_service = ModerationAuditService(db)

    case = await service.resolve_case(case_id, outcome_code, outcome_summary, str(current_user.id))

    await audit_service.log_moderation_action(
        action="case_resolved",
        actor_user_id=str(current_user.id),
        resource_type="moderation_case",
        resource_id=case_id,
        metadata={"outcome_code": outcome_code}
    )

    await audit_service.log_case_event(
        case_id=case_id,
        event_type=ModerationCaseEventType.RESOLVED,
        actor_user_id=str(current_user.id),
        payload={"outcome_code": outcome_code, "summary": outcome_summary}
    )

    await db.commit()
    return {"id": case.id, "status": case.status, "closed_at": case.closed_at}


@router.post("/cases/{case_id}/dismiss")
async def dismiss_case(
    case_id: str,
    outcome_summary: str,
    current_user: User = Depends(require_admin_moderation),
    db: AsyncSession = Depends(get_db)
):
    service = ModerationCaseService(db)
    audit_service = ModerationAuditService(db)

    case = await service.dismiss_case(case_id, outcome_summary, str(current_user.id))

    await audit_service.log_moderation_action(
        action="case_dismissed",
        actor_user_id=str(current_user.id),
        resource_type="moderation_case",
        resource_id=case_id
    )

    await audit_service.log_case_event(
        case_id=case_id,
        event_type=ModerationCaseEventType.DISMISSED,
        actor_user_id=str(current_user.id),
        payload={"summary": outcome_summary}
    )

    await db.commit()
    return {"id": case.id, "status": case.status, "closed_at": case.closed_at}


# REVIEWS
@router.get("/reviews", response_model=List[ReviewListResponse])
async def list_reviews(
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    current_user: User = Depends(require_admin_moderation),
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import select
    from app.models.step6_models import AppointmentReview

    result = await db.execute(
        select(AppointmentReview)
        .where(AppointmentReview.deleted_at.is_(None))
        .order_by(AppointmentReview.created_at.desc())
        .limit(limit).offset(offset)
    )
    reviews = result.scalars().all()

    return [
        ReviewListResponse(
            id=r.id, appointment_id=r.appointment_id,
            reviewer_user_id=r.reviewer_user_id, reviewer_role_code=r.reviewer_role_code,
            target_user_id=r.target_user_id, target_role_code=r.target_role_code,
            rating_overall=r.rating_overall,
            rating_punctuality=r.rating_punctuality,
            rating_communication=r.rating_communication,
            rating_respect=r.rating_respect,
            comment_text=r.comment_text,
            visibility=r.visibility, status=r.status,
            moderation_flag=r.moderation_flag,
            created_at=r.created_at
        )
        for r in reviews
    ]


@router.post("/reviews/{review_id}/hide")
async def hide_review(
    review_id: str,
    data: ReviewHideRestore,
    current_user: User = Depends(require_admin_moderation),
    db: AsyncSession = Depends(get_db)
):
    service = ReviewService(db)
    rep_service = ReputationService(db)
    audit_service = ModerationAuditService(db)

    review = await service.hide_review(review_id, str(current_user.id))
    await rep_service.recalculate_reputation(review.target_user_id)

    await audit_service.log_moderation_action(
        action="review_hidden",
        actor_user_id=str(current_user.id),
        resource_type="appointment_review",
        resource_id=review_id,
        metadata={"reason": data.reason}
    )
    await db.commit()
    return {"id": review.id, "status": review.status}


@router.post("/reviews/{review_id}/restore")
async def restore_review(
    review_id: str,
    data: ReviewHideRestore,
    current_user: User = Depends(require_admin_moderation),
    db: AsyncSession = Depends(get_db)
):
    service = ReviewService(db)
    rep_service = ReputationService(db)
    audit_service = ModerationAuditService(db)

    review = await service.restore_review(review_id, str(current_user.id))
    await rep_service.recalculate_reputation(review.target_user_id)

    await audit_service.log_moderation_action(
        action="review_restored",
        actor_user_id=str(current_user.id),
        resource_type="appointment_review",
        resource_id=review_id
    )
    await db.commit()
    return {"id": review.id, "status": review.status}


# SANCTIONS
@router.get("/sanctions", response_model=List[SanctionResponse])
async def list_sanctions(
    target_type: Optional[str] = Query(None),
    target_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    current_user: User = Depends(require_admin_moderation),
    db: AsyncSession = Depends(get_db)
):
    service = SanctionService(db)
    sanctions = await service.list_sanctions(
        target_type=target_type, target_id=target_id,
        status_filter=status, limit=limit, offset=offset
    )
    return [
        SanctionResponse(
            id=s.id, target_type=s.target_type, target_id=s.target_id,
            sanction_type=s.sanction_type, reason_code=s.reason_code,
            reason_text=s.reason_text,
            starts_at=s.starts_at, ends_at=s.ends_at,
            status=s.status,
            applied_by_user_id=s.applied_by_user_id,
            lifted_by_user_id=s.lifted_by_user_id,
            lifted_reason=s.lifted_reason,
            moderation_case_id=s.moderation_case_id
        )
        for s in sanctions
    ]


@router.post("/sanctions")
async def create_sanction(
    data: SanctionCreate,
    current_user: User = Depends(require_admin_moderation),
    db: AsyncSession = Depends(get_db)
):
    service = SanctionService(db)
    audit_service = ModerationAuditService(db)

    sanction = await service.create_sanction(
        target_type=data.target_type,
        target_id=data.target_id,
        sanction_type=data.sanction_type,
        reason_code=data.reason_code,
        reason_text=data.reason_text,
        starts_at=data.starts_at,
        ends_at=data.ends_at,
        applied_by_user_id=str(current_user.id),
        moderation_case_id=data.moderation_case_id
    )

    await audit_service.log_moderation_action(
        action="sanction_applied",
        actor_user_id=str(current_user.id),
        resource_type="account_sanction",
        resource_id=sanction.id,
        metadata={"target_type": data.target_type, "sanction_type": data.sanction_type}
    )
    await db.commit()
    return {"sanction_id": sanction.id, "status": sanction.status}


@router.post("/sanctions/{sanction_id}/lift")
async def lift_sanction(
    sanction_id: str,
    data: SanctionLift,
    current_user: User = Depends(require_admin_moderation),
    db: AsyncSession = Depends(get_db)
):
    service = SanctionService(db)
    audit_service = ModerationAuditService(db)

    sanction = await service.lift_sanction(sanction_id, str(current_user.id), data.reason)

    await audit_service.log_moderation_action(
        action="sanction_lifted",
        actor_user_id=str(current_user.id),
        resource_type="account_sanction",
        resource_id=sanction_id,
        metadata={"reason": data.reason}
    )
    await db.commit()
    return {"id": sanction.id, "status": sanction.status}
