from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.core.clinical_authorization import require_professional_appointment
from app.models.step2_models import Appointment
from app.models.step4_models import ClinicalAccessAuditAction
from app.schemas.step4_schemas import (
    ClinicalNoteUpdate, ClinicalNoteResponse,
    PrescriptionCreate, PrescriptionUpdate, PrescriptionResponse, PrescriptionItemResponse,
    CareInstructionUpdate, CareInstructionResponse,
    ClinicalFileCreate, ClinicalFileResponse
)
from app.services.step4_services import (
    ClinicalNoteService, PrescriptionService,
    CareInstructionService, ClinicalFileService, ClinicalAuditService
)

router = APIRouter()


@router.get("/me/appointments/{appointment_id}/clinical-note")
async def get_clinical_note(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    appt = await require_professional_appointment(appointment_id, current_user, db)
    
    service = ClinicalNoteService(db)
    note = await service.get_or_create_note(appointment_id, appt.professional_id, appt.patient_id)
    
    audit_service = ClinicalAuditService(db)
    await audit_service.log_access(
        resource_type="clinical_note",
        resource_id=note.id,
        actor_user_id=str(current_user.id),
        actor_role_code="professional",
        action=ClinicalAccessAuditAction.READ,
        appointment_id=appointment_id
    )
    await db.commit()
    
    return ClinicalNoteResponse(
        id=note.id,
        appointment_id=note.appointment_id,
        note_status=note.note_status,
        reason_for_consultation=note.reason_for_consultation,
        subjective_summary=note.subjective_summary,
        objective_summary=note.objective_summary,
        assessment=note.assessment,
        plan=note.plan,
        visible_to_patient=note.visible_to_patient,
        version=note.version
    )


@router.put("/me/appointments/{appointment_id}/clinical-note")
async def update_clinical_note(
    appointment_id: str,
    data: ClinicalNoteUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    appt = await require_professional_appointment(appointment_id, current_user, db)
    
    service = ClinicalNoteService(db)
    note = await service.update_note(appointment_id, appt.professional_id, appt.patient_id, data)
    
    audit_service = ClinicalAuditService(db)
    await audit_service.log_access(
        resource_type="clinical_note",
        resource_id=note.id,
        actor_user_id=str(current_user.id),
        actor_role_code="professional",
        action=ClinicalAccessAuditAction.UPDATE,
        appointment_id=appointment_id
    )
    await db.commit()
    
    return ClinicalNoteResponse(
        id=note.id,
        appointment_id=note.appointment_id,
        note_status=note.note_status,
        reason_for_consultation=note.reason_for_consultation,
        subjective_summary=note.subjective_summary,
        objective_summary=note.objective_summary,
        assessment=note.assessment,
        plan=note.plan,
        visible_to_patient=note.visible_to_patient,
        version=note.version
    )


@router.post("/me/appointments/{appointment_id}/clinical-note/sign-simple")
async def sign_clinical_note(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    appt = await require_professional_appointment(appointment_id, current_user, db)
    
    service = ClinicalNoteService(db)
    note = await service.sign_note(appointment_id, appt.professional_id)
    
    audit_service = ClinicalAuditService(db)
    await audit_service.log_access(
        resource_type="clinical_note",
        resource_id=note.id,
        actor_user_id=str(current_user.id),
        actor_role_code="professional",
        action="sign_simple",
        appointment_id=appointment_id
    )
    await db.commit()
    
    return ClinicalNoteResponse(
        id=note.id,
        appointment_id=note.appointment_id,
        note_status=note.note_status,
        reason_for_consultation=note.reason_for_consultation,
        subjective_summary=note.subjective_summary,
        objective_summary=note.objective_summary,
        assessment=note.assessment,
        plan=note.plan,
        visible_to_patient=note.visible_to_patient,
        version=note.version
    )


@router.get("/me/appointments/{appointment_id}/prescription")
async def get_prescription(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    appt = await require_professional_appointment(appointment_id, current_user, db)
    
    service = PrescriptionService(db)
    prescription = await service.get_prescription(appointment_id)
    if not prescription:
        return {"message": "No prescription found"}
    
    items_result = await db.execute(
        select(PrescriptionItemResponse).where(
            PrescriptionItemResponse.prescription_id == prescription.id,
            PrescriptionItemResponse.deleted_at.is_(None)
        )
    )
    items = items_result.scalars().all()
    
    audit_service = ClinicalAuditService(db)
    await audit_service.log_access(
        resource_type="prescription",
        resource_id=prescription.id,
        actor_user_id=str(current_user.id),
        actor_role_code="professional",
        action=ClinicalAccessAuditAction.READ,
        appointment_id=appointment_id
    )
    await db.commit()
    
    return PrescriptionResponse(
        id=prescription.id,
        appointment_id=prescription.appointment_id,
        status=prescription.status,
        issued_at=prescription.issued_at,
        general_notes=prescription.general_notes,
        items_count=prescription.items_count or 0,
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


@router.post("/me/appointments/{appointment_id}/prescription")
async def create_prescription(
    appointment_id: str,
    data: PrescriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    appt = await require_professional_appointment(appointment_id, current_user, db)
    
    service = PrescriptionService(db)
    prescription = await service.create_prescription(
        appointment_id, appt.professional_id, appt.patient_id, data
    )
    
    audit_service = ClinicalAuditService(db)
    await audit_service.log_access(
        resource_type="prescription",
        resource_id=prescription.id,
        actor_user_id=str(current_user.id),
        actor_role_code="professional",
        action=ClinicalAccessAuditAction.CREATE,
        appointment_id=appointment_id
    )
    await db.commit()
    
    return {
        "prescription_id": prescription.id,
        "status": prescription.status,
        "items_count": len(data.items)
    }


@router.put("/me/appointments/{appointment_id}/prescription/{prescription_id}")
async def update_prescription(
    appointment_id: str,
    prescription_id: str,
    data: PrescriptionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    appt = await require_professional_appointment(appointment_id, current_user, db)
    
    service = PrescriptionService(db)
    prescription = await service.update_prescription(appointment_id, data)
    
    audit_service = ClinicalAuditService(db)
    await audit_service.log_access(
        resource_type="prescription",
        resource_id=prescription.id,
        actor_user_id=str(current_user.id),
        actor_role_code="professional",
        action=ClinicalAccessAuditAction.UPDATE,
        appointment_id=appointment_id
    )
    await db.commit()
    
    return {"prescription_id": prescription.id, "status": prescription.status}


@router.post("/me/appointments/{appointment_id}/prescription/{prescription_id}/issue")
async def issue_prescription(
    appointment_id: str,
    prescription_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    appt = await require_professional_appointment(appointment_id, current_user, db)
    
    service = PrescriptionService(db)
    prescription = await service.issue_prescription(appointment_id)
    
    audit_service = ClinicalAuditService(db)
    await audit_service.log_access(
        resource_type="prescription",
        resource_id=prescription.id,
        actor_user_id=str(current_user.id),
        actor_role_code="professional",
        action="issue",
        appointment_id=appointment_id
    )
    await db.commit()
    
    return {"prescription_id": prescription.id, "status": prescription.status}


@router.post("/me/appointments/{appointment_id}/prescription/{prescription_id}/revoke")
async def revoke_prescription(
    appointment_id: str,
    prescription_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    appt = await require_professional_appointment(appointment_id, current_user, db)
    
    service = PrescriptionService(db)
    prescription = await service.revoke_prescription(appointment_id)
    
    audit_service = ClinicalAuditService(db)
    await audit_service.log_access(
        resource_type="prescription",
        resource_id=prescription.id,
        actor_user_id=str(current_user.id),
        actor_role_code="professional",
        action=ClinicalAccessAuditAction.REVOKE,
        appointment_id=appointment_id
    )
    await db.commit()
    
    return {"prescription_id": prescription.id, "status": prescription.status}


@router.get("/me/appointments/{appointment_id}/care-instructions")
async def get_care_instructions(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    appt = await require_professional_appointment(appointment_id, current_user, db)
    
    service = CareInstructionService(db)
    instruction = await service.upsert_instruction(
        appointment_id, appt.professional_id, appt.patient_id,
        CareInstructionUpdate(content="", follow_up_recommended=False)
    )
    
    audit_service = ClinicalAuditService(db)
    await audit_service.log_access(
        resource_type="care_instruction",
        resource_id=instruction.id,
        actor_user_id=str(current_user.id),
        actor_role_code="professional",
        action=ClinicalAccessAuditAction.READ,
        appointment_id=appointment_id
    )
    await db.commit()
    
    return CareInstructionResponse(
        id=instruction.id,
        appointment_id=instruction.appointment_id,
        status=instruction.status,
        content=instruction.content,
        follow_up_recommended=instruction.follow_up_recommended,
        follow_up_note=instruction.follow_up_note
    )


@router.put("/me/appointments/{appointment_id}/care-instructions")
async def update_care_instructions(
    appointment_id: str,
    data: CareInstructionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    appt = await require_professional_appointment(appointment_id, current_user, db)
    
    service = CareInstructionService(db)
    instruction = await service.upsert_instruction(
        appointment_id, appt.professional_id, appt.patient_id, data
    )
    
    audit_service = ClinicalAuditService(db)
    await audit_service.log_access(
        resource_type="care_instruction",
        resource_id=instruction.id,
        actor_user_id=str(current_user.id),
        actor_role_code="professional",
        action=ClinicalAccessAuditAction.UPDATE,
        appointment_id=appointment_id
    )
    await db.commit()
    
    return CareInstructionResponse(
        id=instruction.id,
        appointment_id=instruction.appointment_id,
        status=instruction.status,
        content=instruction.content,
        follow_up_recommended=instruction.follow_up_recommended,
        follow_up_note=instruction.follow_up_note
    )


@router.post("/me/appointments/{appointment_id}/care-instructions/issue")
async def issue_care_instructions(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    appt = await require_professional_appointment(appointment_id, current_user, db)
    
    service = CareInstructionService(db)
    instruction = await service.issue_instruction(appointment_id)
    
    audit_service = ClinicalAuditService(db)
    await audit_service.log_access(
        resource_type="care_instruction",
        resource_id=instruction.id,
        actor_user_id=str(current_user.id),
        actor_role_code="professional",
        action="issue",
        appointment_id=appointment_id
    )
    await db.commit()
    
    return CareInstructionResponse(
        id=instruction.id,
        appointment_id=instruction.appointment_id,
        status=instruction.status,
        content=instruction.content,
        follow_up_recommended=instruction.follow_up_recommended,
        follow_up_note=instruction.follow_up_note
    )


@router.post("/me/appointments/{appointment_id}/clinical-files")
async def create_clinical_file(
    appointment_id: str,
    data: ClinicalFileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    appt = await require_professional_appointment(appointment_id, current_user, db)
    
    service = ClinicalFileService(db)
    file_record = await service.create_clinical_file(appointment_id, str(current_user.id), data)
    
    audit_service = ClinicalAuditService(db)
    await audit_service.log_access(
        resource_type="clinical_file",
        resource_id=file_record.id,
        actor_user_id=str(current_user.id),
        actor_role_code="professional",
        action=ClinicalAccessAuditAction.CREATE,
        appointment_id=appointment_id
    )
    await db.commit()
    
    return ClinicalFileResponse(
        id=file_record.id,
        appointment_id=file_record.appointment_id,
        file_id=file_record.file_id,
        file_type=file_record.file_type,
        is_visible_to_patient=file_record.is_visible_to_patient,
        status=file_record.status,
        created_at=file_record.created_at
    )


@router.get("/me/appointments/{appointment_id}/clinical-files")
async def list_clinical_files(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    appt = await require_professional_appointment(appointment_id, current_user, db)
    
    service = ClinicalFileService(db)
    files = await service.list_files(appointment_id)
    
    audit_service = ClinicalAuditService(db)
    for f in files:
        await audit_service.log_access(
            resource_type="clinical_file",
            resource_id=f.id,
            actor_user_id=str(current_user.id),
            actor_role_code="professional",
            action=ClinicalAccessAuditAction.LIST,
            appointment_id=appointment_id
        )
    await db.commit()
    
    return [
        ClinicalFileResponse(
            id=f.id,
            appointment_id=f.appointment_id,
            file_id=f.file_id,
            file_type=f.file_type,
            is_visible_to_patient=f.is_visible_to_patient,
            status=f.status,
            created_at=f.created_at
        ) for f in files
    ]


@router.delete("/me/appointments/{appointment_id}/clinical-files/{file_id}")
async def delete_clinical_file(
    appointment_id: str,
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    appt = await require_professional_appointment(appointment_id, current_user, db)
    
    service = ClinicalFileService(db)
    file_record = await service.delete_file(appointment_id, file_id)
    
    audit_service = ClinicalAuditService(db)
    await audit_service.log_access(
        resource_type="clinical_file",
        resource_id=file_record.id,
        actor_user_id=str(current_user.id),
        actor_role_code="professional",
        action=ClinicalAccessAuditAction.UPDATE,
        appointment_id=appointment_id
    )
    await db.commit()
    
    return {"id": file_record.id, "status": file_record.status}
