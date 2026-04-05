from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.models.step4_models import ClinicalAccessAudit
from app.models.step2_models import Appointment
from app.services.step4_services import TeleconsultationSessionService
from app.schemas.step4_schemas import TeleconsultationMetaResponse, ClinicalAccessAuditResponse

router = APIRouter()


@router.get("/appointments/{appointment_id}/teleconsultation-meta")
async def get_teleconsultation_meta(
    appointment_id: str,
    current_user: User = Depends(require_role(["super_admin", "admin_validation", "admin_support"])),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    appt = result.scalar_one_or_none()
    if not appt:
        return {"message": "Appointment not found"}
    
    service = TeleconsultationSessionService(db)
    session = await service.get_session(appointment_id)
    
    if not session:
        return {"message": "No teleconsultation session"}
    
    return TeleconsultationMetaResponse(
        id=session.id,
        appointment_id=session.appointment_id,
        provider_code=session.provider_code,
        status=session.status,
        scheduled_start=session.scheduled_start,
        scheduled_end=session.scheduled_end,
        actual_start=session.actual_start,
        actual_end=session.actual_end,
        has_active_session=session.status in ["ready", "in_progress"]
    )


@router.get("/clinical-access-audit")
async def get_clinical_access_audit(
    appointment_id: str = Query(None),
    current_user: User = Depends(require_role(["super_admin", "admin_validation", "admin_support"])),
    db: AsyncSession = Depends(get_db)
):
    query = select(ClinicalAccessAudit)
    if appointment_id:
        query = query.where(ClinicalAccessAudit.appointment_id == appointment_id)
    
    query = query.order_by(ClinicalAccessAudit.created_at.desc()).limit(100)
    result = await db.execute(query)
    audits = result.scalars().all()
    
    return [
        ClinicalAccessAuditResponse(
            id=a.id,
            resource_type=a.resource_type,
            resource_id=a.resource_id,
            appointment_id=a.appointment_id,
            actor_user_id=a.actor_user_id,
            actor_role_code=a.actor_role_code,
            action=a.action,
            justification=a.justification,
            created_at=a.created_at
        ) for a in audits
    ]
