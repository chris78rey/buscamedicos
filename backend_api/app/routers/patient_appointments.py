from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.models.role import RoleCode
from app.models.patient import Patient
from app.schemas.step2_schemas import AppointmentCreate
from app.services.step2_services import AppointmentService

router = APIRouter()

@router.post("/appointments")
async def create_appointment(
    data: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    patient_result = await db.execute(select(Patient).where(Patient.user_id == current_user.id))
    patient = patient_result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    if data.professional_id == patient.id:
        raise HTTPException(status_code=400, detail="Cannot book with yourself")
    
    try:
        apt = await AppointmentService.create_appointment(
            db,
            patient_id=patient.id,
            professional_id=data.professional_id,
            modality_code=data.modality_code,
            scheduled_start=data.scheduled_start,
            patient_note=data.patient_note
        )
        return {
            "id": apt.id,
            "public_code": apt.public_code,
            "status": apt.status,
            "scheduled_start": apt.scheduled_start.isoformat(),
            "scheduled_end": apt.scheduled_end.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/appointments")
async def get_my_appointments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    patient_result = await db.execute(select(Patient).where(Patient.user_id == current_user.id))
    patient = patient_result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    from app.models.step2_models import Appointment
    result = await db.execute(
        select(Appointment).where(
            Appointment.patient_id == patient.id,
            Appointment.deleted_at.is_(None)
        ).order_by(Appointment.scheduled_start.desc())
    )
    return result.scalars().all()

@router.get("/appointments/{appointment_id}")
async def get_appointment(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    patient_result = await db.execute(select(Patient).where(Patient.user_id == current_user.id))
    patient = patient_result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    from app.models.step2_models import Appointment
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.patient_id == patient.id
        )
    )
    apt = result.scalar_one_or_none()
    if not apt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return apt

@router.post("/appointments/{appointment_id}/cancel")
async def cancel_appointment(
    appointment_id: str,
    reason: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    patient_result = await db.execute(select(Patient).where(Patient.user_id == current_user.id))
    patient = patient_result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    from app.models.step2_models import Appointment
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.patient_id == patient.id
        )
    )
    apt = result.scalar_one_or_none()
    if not apt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    try:
        updated = await AppointmentService.transition_appointment(
            db, appointment_id, "cancelled_by_patient", current_user.id, reason
        )
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))