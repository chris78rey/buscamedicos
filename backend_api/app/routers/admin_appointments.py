from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.user import User
from app.models.role import RoleCode
from app.models.audit import AuditEvent

router = APIRouter()

@router.get("/appointments")
async def list_appointments(
    current_user: User = Depends(require_role([RoleCode.ADMIN_VALIDATION, RoleCode.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    from app.models.step2_models import Appointment
    result = await db.execute(
        select(Appointment).where(Appointment.deleted_at.is_(None)).order_by(Appointment.scheduled_start.desc())
    )
    return result.scalars().all()

@router.get("/appointments/{appointment_id}")
async def get_appointment(
    appointment_id: str,
    current_user: User = Depends(require_role([RoleCode.ADMIN_VALIDATION, RoleCode.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    from app.models.step2_models import Appointment
    result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    apt = result.scalar_one_or_none()
    if not apt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {
        "id": apt.id,
        "public_code": apt.public_code,
        "patient_id": apt.patient_id,
        "professional_id": apt.professional_id,
        "modality_code": apt.modality_code,
        "scheduled_start": apt.scheduled_start,
        "scheduled_end": apt.scheduled_end,
        "status": apt.status,
        "admin_note": apt.admin_note,
        "created_at": apt.created_at
    }

@router.get("/audit-events")
async def get_appointment_audit_events(
    entity_type: str = "appointment",
    current_user: User = Depends(require_role([RoleCode.ADMIN_VALIDATION, RoleCode.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(AuditEvent).where(
            AuditEvent.entity_type == entity_type
        ).order_by(AuditEvent.occurred_at.desc()).limit(100)
    )
    return result.scalars().all()