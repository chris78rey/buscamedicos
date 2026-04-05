import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text
from app.core.database import Base


class TeleconsultationStatus:
    CREATED = "created"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class TeleconsultationSession(Base):
    __tablename__ = "teleconsultation_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    appointment_id = Column(String, nullable=False, index=True)
    provider_code = Column(String, nullable=False)
    session_url = Column(Text, nullable=False)
    host_url = Column(Text, nullable=True)
    access_code = Column(String, nullable=True)
    scheduled_start = Column(DateTime, nullable=False)
    scheduled_end = Column(DateTime, nullable=False)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)
    status = Column(String, nullable=False)
    created_by_user_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")


class ClinicalNoteStatus:
    DRAFT = "draft"
    SIGNED_SIMPLE = "signed_simple"
    AMENDED = "amended"


class ClinicalNoteSimple(Base):
    __tablename__ = "clinical_notes_simple"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    appointment_id = Column(String, unique=True, nullable=False, index=True)
    professional_id = Column(String, nullable=False)
    patient_id = Column(String, nullable=False)
    note_status = Column(String, nullable=False)
    reason_for_consultation = Column(Text, nullable=True)
    subjective_summary = Column(Text, nullable=True)
    objective_summary = Column(Text, nullable=True)
    assessment = Column(Text, nullable=True)
    plan = Column(Text, nullable=True)
    private_professional_note = Column(Text, nullable=True)
    visible_to_patient = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")


class ClinicalNoteVersion(Base):
    __tablename__ = "clinical_note_versions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    clinical_note_id = Column(String, nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    snapshot_json = Column(Text, nullable=False)
    changed_by_user_id = Column(String, nullable=False)
    change_reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PrescriptionStatus:
    DRAFT = "draft"
    ISSUED = "issued"
    REVOKED = "revoked"


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    appointment_id = Column(String, nullable=False, index=True)
    professional_id = Column(String, nullable=False)
    patient_id = Column(String, nullable=False)
    status = Column(String, nullable=False)
    issued_at = Column(DateTime, nullable=True)
    general_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")


class PrescriptionItem(Base):
    __tablename__ = "prescription_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    prescription_id = Column(String, nullable=False, index=True)
    medication_name = Column(String, nullable=False)
    presentation = Column(String, nullable=True)
    dosage = Column(String, nullable=False)
    frequency = Column(String, nullable=False)
    duration = Column(String, nullable=False)
    route = Column(String, nullable=True)
    instructions = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")


class CareInstructionStatus:
    DRAFT = "draft"
    ISSUED = "issued"
    AMENDED = "amended"


class CareInstruction(Base):
    __tablename__ = "care_instructions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    appointment_id = Column(String, unique=True, nullable=False, index=True)
    professional_id = Column(String, nullable=False)
    patient_id = Column(String, nullable=False)
    status = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    follow_up_recommended = Column(Boolean, default=False)
    follow_up_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")


class ClinicalFileType:
    RECETA_PDF = "receta_pdf"
    INDICACION_PDF = "indicacion_pdf"
    DOCUMENTO_CLINICO = "documento_clinico"
    IMAGEN_CLINICA = "imagen_clinica"
    OTRO = "otro"


class ClinicalFileStatus:
    ACTIVE = "active"
    DELETED = "deleted"


class ClinicalFile(Base):
    __tablename__ = "clinical_files"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    appointment_id = Column(String, nullable=False, index=True)
    uploaded_by_user_id = Column(String, nullable=False)
    file_id = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    is_visible_to_patient = Column(Boolean, default=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")


class ClinicalAccessAuditAction:
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    REVOKE = "revoke"
    LIST = "list"
    START_SESSION = "start_session"
    END_SESSION = "end_session"


class ClinicalAccessAudit(Base):
    __tablename__ = "clinical_access_audit"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_type = Column(String, nullable=False)
    resource_id = Column(String, nullable=False)
    appointment_id = Column(String, nullable=True, index=True)
    actor_user_id = Column(String, nullable=False)
    actor_role_code = Column(String, nullable=False)
    action = Column(String, nullable=False)
    justification = Column(Text, nullable=True)
    request_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ConsultationStatus:
    NOT_STARTED = "not_started"
    TELECONSULT_READY = "teleconsult_ready"
    IN_CONSULTATION = "in_consultation"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
