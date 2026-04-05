from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.step6_services import ReportService, ModerationAuditService
from app.schemas.step6_schemas import SafetyReportCreate, SafetyReportResponse

router = APIRouter()


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
