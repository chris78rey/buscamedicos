from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.step2_models import Appointment, AppointmentStatus
from app.services.step6_services import ReviewService, ReputationService, ReportService, ModerationAuditService
from app.schemas.step6_schemas import (
    ReviewPatientProfessionalCreate, ReviewEligibilityResponse,
    SafetyReportCreate, SafetyReportResponse, ReviewResponse
)

router = APIRouter()


@router.get("/review-eligibility", response_model=List[ReviewEligibilityResponse])
async def get_review_eligibility(
    professional_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    patient_id = str(current_user.id)

    query = select(Appointment).where(
        Appointment.patient_id == patient_id,
        Appointment.status == AppointmentStatus.COMPLETED,
        Appointment.deleted_at.is_(None)
    )
    if professional_id:
        query = query.where(Appointment.professional_id == professional_id)

    result = await db.execute(query)
    appointments = result.scalars().all()

    review_service = ReviewService(db)
    eligibility = []
    for appt in appointments:
        existing_result = await db.execute(
            select(Appointment).where(
                Appointment.id == appt.id
            )
        )
        can_review = not getattr(appt, 'patient_review_submitted', False)
        eligibility.append({
            "appointment_id": appt.id,
            "can_review_professional": can_review,
            "reason": None if can_review else "Review already submitted"
        })

    return eligibility


@router.post("/appointments/{appointment_id}/review-professional")
async def review_professional(
    appointment_id: str,
    data: ReviewPatientProfessionalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    appt_result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    appt = appt_result.scalar_one_or_none()
    if not appt or appt.deleted_at:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appt.status != AppointmentStatus.COMPLETED:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=400, detail="Only completed appointments can be reviewed")

    patient_id = str(current_user.id)
    professional_id = str(appt.professional_id)

    review_service = ReviewService(db)
    rep_service = ReputationService(db)
    audit_service = ModerationAuditService(db)

    review = await review_service.create_patient_review(
        appointment_id, patient_id, professional_id, data
    )

    await rep_service.recalculate_reputation(professional_id)

    await audit_service.log_moderation_action(
        action="review_created",
        actor_user_id=patient_id,
        resource_type="appointment_review",
        resource_id=review.id,
        metadata={"appointment_id": appointment_id, "visibility": "public"}
    )

    await db.commit()

    return {
        "review_id": review.id,
        "status": review.status,
        "visibility": review.visibility,
        "target_user_id": review.target_user_id
    }


@router.get("/reviews/me", response_model=List[ReviewResponse])
async def get_my_reviews(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ReviewService(db)
    reviews = await service.get_my_reviews(str(current_user.id))
    return [
        ReviewResponse(
            id=r.id, appointment_id=r.appointment_id,
            reviewer_user_id=r.reviewer_user_id, reviewer_role_code=r.reviewer_role_code,
            target_user_id=r.target_user_id, target_role_code=r.target_role_code,
            rating_overall=r.rating_overall,
            rating_punctuality=r.rating_punctuality,
            rating_communication=r.rating_communication,
            rating_respect=r.rating_respect,
            comment_text=r.comment_text,
            visibility=r.visibility, status=r.status,
            created_at=r.created_at
        )
        for r in reviews
    ]


@router.post("/reports")
async def create_report(
    data: SafetyReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ReportService(db)
    audit_service = ModerationAuditService(db)

    report = await service.create_report(str(current_user.id), data)

    await audit_service.log_moderation_action(
        action="report_created",
        actor_user_id=str(current_user.id),
        resource_type="safety_report",
        resource_id=report.id,
        metadata={"subject_type": data.subject_type, "category_code": data.category_code}
    )

    await db.commit()

    return {
        "report_id": report.id,
        "status": report.status,
        "submitted_at": report.submitted_at
    }


@router.get("/reports/me", response_model=List[SafetyReportResponse])
async def get_my_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ReportService(db)
    reports = await service.get_reports_by_reporter(str(current_user.id))
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
async def get_report_detail(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ReportService(db)
    audit_service = ModerationAuditService(db)

    report = await service.get_report(report_id)
    if not report:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=404, detail="Report not found")
    if report.reporter_user_id != str(current_user.id):
        from fastapi import HTTPException, status
        raise HTTPException(status_code=403, detail="Not your report")

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
