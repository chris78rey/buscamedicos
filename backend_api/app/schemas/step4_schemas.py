from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TeleconsultationCreate(BaseModel):
    provider_code: str
    session_url: str
    host_url: Optional[str] = None
    access_code: Optional[str] = None
    scheduled_start: datetime
    scheduled_end: datetime


class TeleconsultationResponse(BaseModel):
    id: str
    appointment_id: str
    provider_code: str
    session_url: str
    host_url: Optional[str] = None
    access_code: Optional[str] = None
    scheduled_start: datetime
    scheduled_end: datetime
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    status: str


class TeleconsultationMetaResponse(BaseModel):
    id: str
    appointment_id: str
    provider_code: str
    status: str
    scheduled_start: datetime
    scheduled_end: datetime
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    has_active_session: bool


class ClinicalNoteUpdate(BaseModel):
    reason_for_consultation: Optional[str] = None
    subjective_summary: Optional[str] = None
    objective_summary: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    private_professional_note: Optional[str] = None
    visible_to_patient: bool = False
    change_reason: Optional[str] = None


class ClinicalNoteResponse(BaseModel):
    id: str
    appointment_id: str
    note_status: str
    reason_for_consultation: Optional[str] = None
    subjective_summary: Optional[str] = None
    objective_summary: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    visible_to_patient: bool
    version: str


class ClinicalNotePatientResponse(BaseModel):
    appointment_id: str
    visible_to_patient: bool
    reason_for_consultation: Optional[str] = None
    subjective_summary: Optional[str] = None
    objective_summary: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None


class PrescriptionItemCreate(BaseModel):
    medication_name: str
    presentation: Optional[str] = None
    dosage: str
    frequency: str
    duration: str
    route: Optional[str] = None
    instructions: Optional[str] = None


class PrescriptionCreate(BaseModel):
    general_notes: Optional[str] = None
    items: List[PrescriptionItemCreate]


class PrescriptionUpdate(BaseModel):
    general_notes: Optional[str] = None
    items: List[PrescriptionItemCreate]


class PrescriptionItemResponse(BaseModel):
    id: str
    medication_name: str
    presentation: Optional[str] = None
    dosage: str
    frequency: str
    duration: str
    route: Optional[str] = None
    instructions: Optional[str] = None


class PrescriptionResponse(BaseModel):
    id: str
    appointment_id: str
    status: str
    issued_at: Optional[datetime] = None
    general_notes: Optional[str] = None
    items_count: int
    items: List[PrescriptionItemResponse] = []


class PrescriptionPatientResponse(BaseModel):
    id: str
    appointment_id: str
    status: str
    issued_at: Optional[datetime] = None
    general_notes: Optional[str] = None
    items: List[PrescriptionItemResponse] = []


class CareInstructionUpdate(BaseModel):
    content: str
    follow_up_recommended: bool = False
    follow_up_note: Optional[str] = None


class CareInstructionResponse(BaseModel):
    id: str
    appointment_id: str
    status: str
    content: str
    follow_up_recommended: bool
    follow_up_note: Optional[str] = None


class CareInstructionPatientResponse(BaseModel):
    id: str
    appointment_id: str
    status: str
    content: str
    follow_up_recommended: bool
    follow_up_note: Optional[str] = None


class ClinicalFileCreate(BaseModel):
    file_id: str
    file_type: str
    is_visible_to_patient: bool = True


class ClinicalFileResponse(BaseModel):
    id: str
    appointment_id: str
    file_id: str
    file_type: str
    is_visible_to_patient: bool
    status: str
    created_at: datetime


class ClinicalFilePatientResponse(BaseModel):
    id: str
    appointment_id: str
    file_type: str
    is_visible_to_patient: bool
    status: str
    created_at: datetime


class ClinicalAccessAuditResponse(BaseModel):
    id: str
    resource_type: str
    resource_id: str
    appointment_id: Optional[str] = None
    actor_user_id: str
    actor_role_code: str
    action: str
    justification: Optional[str] = None
    created_at: datetime
