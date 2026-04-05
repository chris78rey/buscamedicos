from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.step2_models import Appointment, AppointmentStatus
from app.models.professional import Professional
from app.services.step6_services import ReviewService, ReputationService, ReportService, ModerationAuditService
from app.schemas.step6_schemas import (
    ReviewProfessionalPatientCreate, ReputationSummaryResponse,
    SafetyReportCreate, SafetyReportResponse, ReviewResponse
)

router = APIRouter()


@router.post("/me/appointments/{appointment_id}/review-patient")
async def review_patient(
    appointment_id: str,
    data: ReviewProfessionalPatientCreate,
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

    professional_id = str(current_user.id)
    patient_id = str(appt.patient_id)

    review_service = ReviewService(db)
    audit_service = ModerationAuditService(db)

    review = await review_service.create_professional_review(
        appointment_id, professional_id, patient_id, data
    )

    await audit_service.log_moderation_action(
        action="review_created",
        actor_user_id=professional_id,
        resource_type="appointment_review",
        resource_id=review.id,
        metadata={"appointment_id": appointment_id, "visibility": "internal_only"}
    )

    await db.commit()

    return {
        "review_id": review.id,
        "status": review.status,
        "visibility": review.visibility
    }


@router.get("/me/reviews/public", response_model=List[ReviewResponse])
async def get_my_public_reviews(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ReviewService(db)
    reviews = await service.get_public_reviews(str(current_user.id))
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


@router.get("/me/reputation-summary")
async def get_my_reputation_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    rep_service = ReputationService(db)
    stats = await rep_service.get_reputation(str(current_user.id))

    if not stats:
        return {
            "professional_id": str(current_user.id),
            "public_reviews_count": 0,
            "avg_overall": 0.0,
            "avg_punctuality": None,
            "avg_communication": None,
            "avg_respect": None
        }

    return {
        "professional_id": str(current_user.id),
        "public_reviews_count": stats.public_reviews_count,
        "avg_overall": float(stats.avg_overall or 0),
        "avg_punctuality": float(stats.avg_punctuality) if stats.avg_punctuality else None,
        "avg_communication": float(stats.avg_communication) if stats.avg_communication else None,
        "avg_respect": float(stats.avg_respect) if stats.avg_respect else None
    }


@router.post("/me/reports")
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


@router.get("/me/reports/me", response_model=List[SafetyReportResponse])
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


@router.get("/me/reports/{report_id}", response_model=SafetyReportResponse)
async def get_report_detail(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ReportService(db)
    report = await service.get_report(report_id)
    if not report:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=404, detail="Report not found")
    if report.reporter_user_id != str(current_user.id):
        from fastapi import HTTPException, status
        raise HTTPException(status_code=403, detail="Not your report")

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
