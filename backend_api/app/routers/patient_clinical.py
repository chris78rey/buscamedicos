from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.core.clinical_authorization import require_patient_appointment
from app.models.step4_models import ClinicalAccessAuditAction, PrescriptionItem
from app.schemas.step4_schemas import (
    ClinicalNotePatientResponse,
    PrescriptionPatientResponse, PrescriptionItemResponse,
    CareInstructionPatientResponse,
    ClinicalFilePatientResponse
)
from app.services.step4_services import (
    ClinicalNoteService, PrescriptionService,
    CareInstructionService, ClinicalFileService, ClinicalAuditService
)

router = APIRouter()


@router.get("/appointments/{appointment_id}/clinical-note")
async def get_patient_clinical_note(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    appt = await require_patient_appointment(appointment_id, current_user, db)
    
    service = ClinicalNoteService(db)
    note = await service.get_or_create_note(appointment_id, "", appt.patient_id)
    
    if not note.visible_to_patient:
        raise HTTPException(status_code=403, detail="Clinical note not visible to patient")
    
    audit_service = ClinicalAuditService(db)
    await audit_service.log_access(
        resource_type="clinical_note",
        resource_id=note.id,
        actor_user_id=str(current_user.id),
        actor_role_code="patient",
        action=ClinicalAccessAuditAction.READ,
        appointment_id=appointment_id
    )
    await db.commit()
    
    return ClinicalNotePatientResponse(
        appointment_id=note.appointment_id,
        visible_to_patient=note.visible_to_patient,
        reason_for_consultation=note.reason_for_consultation,
        subjective_summary=note.subjective_summary,
        objective_summary=note.objective_summary,
        assessment=note.assessment,
        plan=note.plan
    )


@router.get("/appointments/{appointment_id}/prescription")
async def get_patient_prescription(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    appt = await require_patient_appointment(appointment_id, current_user, db)
    
    service = PrescriptionService(db)
    prescription = await service.get_prescription(appointment_id)
    if not prescription:
        return {"message": "No prescription found"}
    
    items_result = await db.execute(
        select(PrescriptionItem).where(
            PrescriptionItem.prescription_id == prescription.id,
            PrescriptionItem.deleted_at.is_(None)
        )
    )
    items = items_result.scalars().all()
    
    audit_service = ClinicalAuditService(db)
    await audit_service.log_access(
        resource_type="prescription",
        resource_id=prescription.id,
        actor_user_id=str(current_user.id),
        actor_role_code="patient",
        action=ClinicalAccessAuditAction.READ,
        appointment_id=appointment_id
    )
    await db.commit()
    
    return PrescriptionPatientResponse(
        id=prescription.id,
        appointment_id=prescription.appointment_id,
        status=prescription.status,
        issued_at=prescription.issued_at,
        general_notes=prescription.general_notes,
        items=[
            PrescriptionItemResponse(
                id=i.id,
                medication_name=i.medication_name,
                presentation=i.presentation,
                dosage=i.dosage,
                frequency=i.frequency,
                duration=i.duration,
                route=i.route,
                instructions=i.instructions
            ) for i in items
        ]
    )


@router.get("/appointments/{appointment_id}/care-instructions")
async def get_patient_care_instructions(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    appt = await require_patient_appointment(appointment_id, current_user, db)
    
    service = CareInstructionService(db)
    instruction = await service.upsert_instruction(
        appointment_id, "", appt.patient_id,
        CareInstructionUpdate(content="", follow_up_recommended=False)
    )
    
    audit_service = ClinicalAuditService(db)
    await audit_service.log_access(
        resource_type="care_instruction",
        resource_id=instruction.id,
        actor_user_id=str(current_user.id),
        actor_role_code="patient",
        action=ClinicalAccessAuditAction.READ,
        appointment_id=appointment_id
    )
    await db.commit()
    
    return CareInstructionPatientResponse(
        id=instruction.id,
        appointment_id=instruction.appointment_id,
        status=instruction.status,
        content=instruction.content,
        follow_up_recommended=instruction.follow_up_recommended,
        follow_up_note=instruction.follow_up_note
    )


@router.get("/appointments/{appointment_id}/clinical-files")
async def get_patient_clinical_files(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    appt = await require_patient_appointment(appointment_id, current_user, db)
    
    service = ClinicalFileService(db)
    files = await service.list_files(appointment_id)
    visible_files = [f for f in files if f.is_visible_to_patient]
    
    for f in visible_files:
        audit_service = ClinicalAuditService(db)
        await audit_service.log_access(
            resource_type="clinical_file",
            resource_id=f.id,
            actor_user_id=str(current_user.id),
            actor_role_code="patient",
            action=ClinicalAccessAuditAction.READ,
            appointment_id=appointment_id
        )
    await db.commit()
    
    return [
        ClinicalFilePatientResponse(
            id=f.id,
            appointment_id=f.appointment_id,
            file_type=f.file_type,
            is_visible_to_patient=f.is_visible_to_patient,
            status=f.status,
            created_at=f.created_at
        ) for f in visible_files
    ]


from fastapi import HTTPException
from app.schemas.step4_schemas import CareInstructionUpdate
