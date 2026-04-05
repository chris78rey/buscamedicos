from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.core.clinical_authorization import require_professional_appointment
from app.models.step2_models import Appointment
from app.models.step4_models import TeleconsultationStatus, ClinicalAccessAuditAction
from app.schemas.step4_schemas import TeleconsultationCreate, TeleconsultationResponse
from app.services.step4_services import TeleconsultationSessionService, ClinicalAuditService

router = APIRouter()


@router.post("/me/appointments/{appointment_id}/teleconsultation")
async def create_teleconsultation(
    appointment_id: str,
    data: TeleconsultationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    appt = await require_professional_appointment(appointment_id, current_user, db)
    
    service = TeleconsultationSessionService(db)
    session = await service.create_session(appointment_id, data, str(current_user.id))
    
    audit_service = ClinicalAuditService(db)
    await audit_service.log_access(
        resource_type="teleconsultation",
        resource_id=session.id,
        actor_user_id=str(current_user.id),
        actor_role_code="professional",
        action=ClinicalAccessAuditAction.CREATE,
        appointment_id=appointment_id
    )
    
    await db.commit()
    return {
        "teleconsultation_session_id": session.id,
        "status": session.status,
        "scheduled_start": session.scheduled_start,
        "scheduled_end": session.scheduled_end
    }


@router.get("/me/appointments/{appointment_id}/teleconsultation")
async def get_teleconsultation(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    appt = await require_professional_appointment(appointment_id, current_user, db)
    
    service = TeleconsultationSessionService(db)
    session = await service.get_session(appointment_id)
    if not session:
        raise HTTPException(status_code=404, detail="Teleconsultation session not found")
    
    audit_service = ClinicalAuditService(db)
    await audit_service.log_access(
        resource_type="teleconsultation",
        resource_id=session.id,
        actor_user_id=str(current_user.id),
        actor_role_code="professional",
        action=ClinicalAccessAuditAction.READ,
        appointment_id=appointment_id
    )
    await db.commit()
    
    return TeleconsultationResponse(
        id=session.id,
        appointment_id=session.appointment_id,
        provider_code=session.provider_code,
        session_url=session.session_url,
        host_url=session.host_url,
        access_code=session.access_code,
        scheduled_start=session.scheduled_start,
        scheduled_end=session.scheduled_end,
        actual_start=session.actual_start,
        actual_end=session.actual_end,
        status=session.status
    )


@router.post("/me/appointments/{appointment_id}/teleconsultation/start")
async def start_teleconsultation(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    appt = await require_professional_appointment(appointment_id, current_user, db)
    
    service = TeleconsultationSessionService(db)
    session = await service.start_session(appointment_id)
    
    audit_service = ClinicalAuditService(db)
    await audit_service.log_access(
        resource_type="teleconsultation",
        resource_id=session.id,
        actor_user_id=str(current_user.id),
        actor_role_code="professional",
        action=ClinicalAccessAuditAction.START_SESSION,
        appointment_id=appointment_id
    )
    
    await db.commit()
    return {"status": session.status, "actual_start": session.actual_start}


@router.post("/me/appointments/{appointment_id}/teleconsultation/end")
async def end_teleconsultation(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    appt = await require_professional_appointment(appointment_id, current_user, db)
    
    service = TeleconsultationSessionService(db)
    session = await service.end_session(appointment_id)
    
    audit_service = ClinicalAuditService(db)
    await audit_service.log_access(
        resource_type="teleconsultation",
        resource_id=session.id,
        actor_user_id=str(current_user.id),
        actor_role_code="professional",
        action=ClinicalAccessAuditAction.END_SESSION,
        appointment_id=appointment_id
    )
    
    await db.commit()
    return {"status": session.status, "actual_end": session.actual_end}


@router.post("/me/appointments/{appointment_id}/teleconsultation/cancel")
async def cancel_teleconsultation(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    appt = await require_professional_appointment(appointment_id, current_user, db)
    
    service = TeleconsultationSessionService(db)
    session = await service.cancel_session(appointment_id)
    
    audit_service = ClinicalAuditService(db)
    await audit_service.log_access(
        resource_type="teleconsultation",
        resource_id=session.id,
        actor_user_id=str(current_user.id),
        actor_role_code="professional",
        action="cancel",
        appointment_id=appointment_id
    )
    
    await db.commit()
    return {"status": session.status}
