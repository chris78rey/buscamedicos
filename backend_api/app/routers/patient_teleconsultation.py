from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.core.clinical_authorization import require_patient_appointment
from app.models.step4_models import ClinicalAccessAuditAction
from app.schemas.step4_schemas import TeleconsultationResponse
from app.services.step4_services import TeleconsultationSessionService, ClinicalAuditService

router = APIRouter()


@router.get("/appointments/{appointment_id}/teleconsultation")
async def get_patient_teleconsultation(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    appt = await require_patient_appointment(appointment_id, current_user, db)
    
    service = TeleconsultationSessionService(db)
    session = await service.get_session(appointment_id)
    if not session:
        return {"message": "No teleconsultation session found"}
    
    audit_service = ClinicalAuditService(db)
    await audit_service.log_access(
        resource_type="teleconsultation",
        resource_id=session.id,
        actor_user_id=str(current_user.id),
        actor_role_code="patient",
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


@router.post("/appointments/{appointment_id}/teleconsultation/join-log")
async def log_teleconsultation_join(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    appt = await require_patient_appointment(appointment_id, current_user, db)
    
    service = TeleconsultationSessionService(db)
    session = await service.get_session(appointment_id)
    if not session:
        return {"message": "No session to join"}
    
    audit_service = ClinicalAuditService(db)
    await audit_service.log_access(
        resource_type="teleconsultation",
        resource_id=session.id,
        actor_user_id=str(current_user.id),
        actor_role_code="patient",
        action="join_session",
        appointment_id=appointment_id
    )
    await db.commit()
    return {"message": "Join logged"}
