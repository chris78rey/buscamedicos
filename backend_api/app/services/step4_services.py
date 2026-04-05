import uuid
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status
from typing import Optional, List, Dict, Any

from app.models.step4_models import (
    TeleconsultationSession, TeleconsultationStatus,
    ClinicalNoteSimple, ClinicalNoteVersion, ClinicalNoteStatus,
    Prescription, PrescriptionItem, PrescriptionStatus,
    CareInstruction, CareInstructionStatus,
    ClinicalFile, ClinicalFileType, ClinicalFileStatus,
    ClinicalAccessAudit, ClinicalAccessAuditAction
)
from app.models.step4_models import ConsultationStatus
from app.models.step2_models import Appointment
from app.schemas.step4_schemas import (
    TeleconsultationCreate, ClinicalNoteUpdate,
    PrescriptionCreate, PrescriptionUpdate,
    CareInstructionUpdate, ClinicalFileCreate
)


class ClinicalAuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_access(
        self,
        resource_type: str,
        resource_id: str,
        actor_user_id: str,
        actor_role_code: str,
        action: str,
        appointment_id: Optional[str] = None,
        justification: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        audit = ClinicalAccessAudit(
            id=str(uuid.uuid4()),
            resource_type=resource_type,
            resource_id=resource_id,
            appointment_id=appointment_id,
            actor_user_id=actor_user_id,
            actor_role_code=actor_role_code,
            action=action,
            justification=justification,
            request_id=request_id,
            created_at=datetime.utcnow()
        )
        self.db.add(audit)
        await self.db.flush()
        return audit


class TeleconsultationSessionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(
        self,
        appointment_id: str,
        data: TeleconsultationCreate,
        user_id: str
    ) -> TeleconsultationSession:
        result = await self.db.execute(
            select(Appointment).where(Appointment.id == appointment_id)
        )
        appt = result.scalar_one_or_none()
        if not appt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
        if appt.deleted_at:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Appointment is deleted")
        if appt.modality_code != "teleconsulta":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only teleconsulta appointments can have sessions")
        if getattr(appt, 'financial_status', None) != "paid":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Appointment must be paid")
        
        existing = await self.db.execute(
            select(TeleconsultationSession).where(
                TeleconsultationSession.appointment_id == appointment_id,
                TeleconsultationSession.deleted_at.is_(None)
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active session already exists")
        
        session = TeleconsultationSession(
            id=str(uuid.uuid4()),
            appointment_id=appointment_id,
            provider_code=data.provider_code,
            session_url=data.session_url,
            host_url=data.host_url,
            access_code=data.access_code,
            scheduled_start=data.scheduled_start,
            scheduled_end=data.scheduled_end,
            status=TeleconsultationStatus.CREATED,
            created_by_user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version="1"
        )
        self.db.add(session)
        
        await self.db.execute(
            update(Appointment)
            .where(Appointment.id == appointment_id)
            .values(consultation_status=ConsultationStatus.TELECONSULT_READY)
        )
        
        await self.db.flush()
        return session

    async def get_session(self, appointment_id: str) -> Optional[TeleconsultationSession]:
        result = await self.db.execute(
            select(TeleconsultationSession).where(
                TeleconsultationSession.appointment_id == appointment_id,
                TeleconsultationSession.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def start_session(self, appointment_id: str) -> TeleconsultationSession:
        session = await self.get_session(appointment_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        if session.status not in [TeleconsultationStatus.READY]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot start session from status {session.status}")
        
        session.status = TeleconsultationStatus.IN_PROGRESS
        session.actual_start = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        
        await self.db.execute(
            update(Appointment)
            .where(Appointment.id == appointment_id)
            .values(consultation_status=ConsultationStatus.IN_CONSULTATION)
        )
        
        await self.db.flush()
        return session

    async def end_session(self, appointment_id: str) -> TeleconsultationSession:
        session = await self.get_session(appointment_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        if session.status != TeleconsultationStatus.IN_PROGRESS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot end session that has not started")
        if not session.actual_start:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot complete teleconsult without actual_start")
        
        session.status = TeleconsultationStatus.COMPLETED
        session.actual_end = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        
        await self.db.execute(
            update(Appointment)
            .where(Appointment.id == appointment_id)
            .values(consultation_status=ConsultationStatus.COMPLETED, has_clinical_content=True)
        )
        
        await self.db.flush()
        return session

    async def cancel_session(self, appointment_id: str) -> TeleconsultationSession:
        session = await self.get_session(appointment_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        if session.status in [TeleconsultationStatus.COMPLETED, TeleconsultationStatus.CANCELLED]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot cancel completed or already cancelled session")
        
        session.status = TeleconsultationStatus.CANCELLED
        session.deleted_at = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        
        await self.db.execute(
            update(Appointment)
            .where(Appointment.id == appointment_id)
            .values(consultation_status=ConsultationStatus.CANCELLED)
        )
        
        await self.db.flush()
        return session


class ClinicalNoteService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_note(self, appointment_id: str, professional_id: str, patient_id: str) -> ClinicalNoteSimple:
        result = await self.db.execute(
            select(ClinicalNoteSimple).where(
                ClinicalNoteSimple.appointment_id == appointment_id,
                ClinicalNoteSimple.deleted_at.is_(None)
            )
        )
        note = result.scalar_one_or_none()
        if note:
            return note
        
        note = ClinicalNoteSimple(
            id=str(uuid.uuid4()),
            appointment_id=appointment_id,
            professional_id=professional_id,
            patient_id=patient_id,
            note_status=ClinicalNoteStatus.DRAFT,
            visible_to_patient=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version="1"
        )
        self.db.add(note)
        await self.db.flush()
        return note

    async def update_note(
        self,
        appointment_id: str,
        professional_id: str,
        patient_id: str,
        data: ClinicalNoteUpdate
    ) -> ClinicalNoteSimple:
        note = await self.get_or_create_note(appointment_id, professional_id, patient_id)
        
        prev_snapshot = {
            "reason_for_consultation": note.reason_for_consultation,
            "subjective_summary": note.subjective_summary,
            "objective_summary": note.objective_summary,
            "assessment": note.assessment,
            "plan": note.plan,
            "private_professional_note": note.private_professional_note,
            "visible_to_patient": note.visible_to_patient,
            "note_status": note.note_status,
            "version": note.version
        }
        
        version_result = await self.db.execute(
            select(ClinicalNoteVersion).where(
                ClinicalNoteVersion.clinical_note_id == note.id
            ).order_by(ClinicalNoteVersion.version_number.desc())
        )
        last_version = version_result.first()
        next_version = (last_version[0].version_number + 1) if last_version else 1
        
        version_record = ClinicalNoteVersion(
            id=str(uuid.uuid4()),
            clinical_note_id=note.id,
            version_number=next_version,
            snapshot_json=json.dumps(prev_snapshot),
            changed_by_user_id=professional_id,
            change_reason=data.change_reason,
            created_at=datetime.utcnow()
        )
        self.db.add(version_record)
        
        if data.reason_for_consultation is not None:
            note.reason_for_consultation = data.reason_for_consultation
        if data.subjective_summary is not None:
            note.subjective_summary = data.subjective_summary
        if data.objective_summary is not None:
            note.objective_summary = data.objective_summary
        if data.assessment is not None:
            note.assessment = data.assessment
        if data.plan is not None:
            note.plan = data.plan
        if data.private_professional_note is not None:
            note.private_professional_note = data.private_professional_note
        if data.visible_to_patient is not None:
            note.visible_to_patient = data.visible_to_patient
        
        note.version = str(int(note.version or "1") + 1)
        note.updated_at = datetime.utcnow()
        
        await self.db.flush()
        return note

    async def sign_note(self, appointment_id: str, professional_id: str) -> ClinicalNoteSimple:
        note = await self.get_or_create_note(appointment_id, professional_id, "")
        if note.note_status == ClinicalNoteStatus.SIGNED_SIMPLE:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Note already signed")
        note.note_status = ClinicalNoteStatus.SIGNED_SIMPLE
        note.updated_at = datetime.utcnow()
        note.version = str(int(note.version or "1") + 1)
        await self.db.flush()
        return note


class PrescriptionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_prescription(
        self,
        appointment_id: str,
        professional_id: str,
        patient_id: str,
        data: PrescriptionCreate
    ) -> Prescription:
        if not data.items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot issue empty prescription")
        
        prescription = Prescription(
            id=str(uuid.uuid4()),
            appointment_id=appointment_id,
            professional_id=professional_id,
            patient_id=patient_id,
            status=PrescriptionStatus.DRAFT,
            general_notes=data.general_notes,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version="1"
        )
        self.db.add(prescription)
        await self.db.flush()
        
        items = []
        for item_data in data.items:
            item = PrescriptionItem(
                id=str(uuid.uuid4()),
                prescription_id=prescription.id,
                medication_name=item_data.medication_name,
                presentation=item_data.presentation,
                dosage=item_data.dosage,
                frequency=item_data.frequency,
                duration=item_data.duration,
                route=item_data.route,
                instructions=item_data.instructions,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                version="1"
            )
            self.db.add(item)
            items.append(item)
        
        await self.db.flush()
        prescription.items_count = len(items)
        return prescription

    async def get_prescription(self, appointment_id: str) -> Optional[Prescription]:
        result = await self.db.execute(
            select(Prescription).where(
                Prescription.appointment_id == appointment_id,
                Prescription.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def update_prescription(
        self,
        appointment_id: str,
        data: PrescriptionUpdate
    ) -> Prescription:
        prescription = await self.get_prescription(appointment_id)
        if not prescription:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found")
        if prescription.status != PrescriptionStatus.DRAFT:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Can only update draft prescriptions")
        
        if data.general_notes is not None:
            prescription.general_notes = data.general_notes
        
        old_items = await self.db.execute(
            select(PrescriptionItem).where(
                PrescriptionItem.prescription_id == prescription.id,
                PrescriptionItem.deleted_at.is_(None)
            )
        )
        for item in old_items.scalars().all():
            item.deleted_at = datetime.utcnow()
            item.updated_at = datetime.utcnow()
        
        for item_data in data.items:
            item = PrescriptionItem(
                id=str(uuid.uuid4()),
                prescription_id=prescription.id,
                medication_name=item_data.medication_name,
                presentation=item_data.presentation,
                dosage=item_data.dosage,
                frequency=item_data.frequency,
                duration=item_data.duration,
                route=item_data.route,
                instructions=item_data.instructions,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                version="1"
            )
            self.db.add(item)
        
        prescription.updated_at = datetime.utcnow()
        prescription.version = str(int(prescription.version or "1") + 1)
        await self.db.flush()
        return prescription

    async def issue_prescription(self, appointment_id: str) -> Prescription:
        prescription = await self.get_prescription(appointment_id)
        if not prescription:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found")
        if prescription.status != PrescriptionStatus.DRAFT:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Can only issue draft prescriptions")
        
        items_result = await self.db.execute(
            select(PrescriptionItem).where(
                PrescriptionItem.prescription_id == prescription.id,
                PrescriptionItem.deleted_at.is_(None)
            )
        )
        items = items_result.scalars().all()
        if not items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot issue empty prescription")
        
        prescription.status = PrescriptionStatus.ISSUED
        prescription.issued_at = datetime.utcnow()
        prescription.updated_at = datetime.utcnow()
        prescription.version = str(int(prescription.version or "1") + 1)
        await self.db.flush()
        return prescription

    async def revoke_prescription(self, appointment_id: str) -> Prescription:
        prescription = await self.get_prescription(appointment_id)
        if not prescription:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found")
        if prescription.status == PrescriptionStatus.REVOKED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Prescription already revoked")
        
        prescription.status = PrescriptionStatus.REVOKED
        prescription.updated_at = datetime.utcnow()
        prescription.version = str(int(prescription.version or "1") + 1)
        await self.db.flush()
        return prescription


class CareInstructionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert_instruction(
        self,
        appointment_id: str,
        professional_id: str,
        patient_id: str,
        data: CareInstructionUpdate
    ) -> CareInstruction:
        result = await self.db.execute(
            select(CareInstruction).where(
                CareInstruction.appointment_id == appointment_id,
                CareInstruction.deleted_at.is_(None)
            )
        )
        instruction = result.scalar_one_or_none()
        
        if not instruction:
            instruction = CareInstruction(
                id=str(uuid.uuid4()),
                appointment_id=appointment_id,
                professional_id=professional_id,
                patient_id=patient_id,
                status=CareInstructionStatus.DRAFT,
                content=data.content,
                follow_up_recommended=data.follow_up_recommended,
                follow_up_note=data.follow_up_note,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                version="1"
            )
            self.db.add(instruction)
        else:
            if data.content:
                instruction.content = data.content
            instruction.follow_up_recommended = data.follow_up_recommended
            instruction.follow_up_note = data.follow_up_note
            instruction.updated_at = datetime.utcnow()
            instruction.version = str(int(instruction.version or "1") + 1)
        
        await self.db.flush()
        return instruction

    async def issue_instruction(self, appointment_id: str) -> CareInstruction:
        result = await self.db.execute(
            select(CareInstruction).where(
                CareInstruction.appointment_id == appointment_id,
                CareInstruction.deleted_at.is_(None)
            )
        )
        instruction = result.scalar_one_or_none()
        if not instruction:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Care instruction not found")
        if not instruction.content:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot issue empty instructions")
        
        instruction.status = CareInstructionStatus.ISSUED
        instruction.updated_at = datetime.utcnow()
        instruction.version = str(int(instruction.version or "1") + 1)
        await self.db.flush()
        return instruction


class ClinicalFileService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_clinical_file(
        self,
        appointment_id: str,
        uploaded_by_user_id: str,
        data: ClinicalFileCreate
    ) -> ClinicalFile:
        file_record = ClinicalFile(
            id=str(uuid.uuid4()),
            appointment_id=appointment_id,
            uploaded_by_user_id=uploaded_by_user_id,
            file_id=data.file_id,
            file_type=data.file_type,
            is_visible_to_patient=data.is_visible_to_patient,
            status=ClinicalFileStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version="1"
        )
        self.db.add(file_record)
        await self.db.flush()
        return file_record

    async def list_files(self, appointment_id: str, include_deleted: bool = False) -> List[ClinicalFile]:
        query = select(ClinicalFile).where(ClinicalFile.appointment_id == appointment_id)
        if not include_deleted:
            query = query.where(ClinicalFile.deleted_at.is_(None))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def delete_file(self, appointment_id: str, file_id: str) -> ClinicalFile:
        result = await self.db.execute(
            select(ClinicalFile).where(
                ClinicalFile.appointment_id == appointment_id,
                ClinicalFile.id == file_id,
                ClinicalFile.deleted_at.is_(None)
            )
        )
        file_record = result.scalar_one_or_none()
        if not file_record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
        
        file_record.status = ClinicalFileStatus.DELETED
        file_record.deleted_at = datetime.utcnow()
        file_record.updated_at = datetime.utcnow()
        await self.db.flush()
        return file_record
