import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer
from app.core.database import Base

class Specialty(Base):
    __tablename__ = "specialties"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")

class ServiceModality(Base):
    __tablename__ = "service_modalities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ProfessionalSpecialty(Base):
    __tablename__ = "professional_specialties"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    professional_id = Column(String, nullable=False, index=True)
    specialty_id = Column(String, nullable=False, index=True)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")

class ProfessionalModality(Base):
    __tablename__ = "professional_modalities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    professional_id = Column(String, nullable=False, index=True)
    modality_id = Column(String, nullable=False, index=True)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")

class ProfessionalPublicProfile(Base):
    __tablename__ = "professional_public_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    professional_id = Column(String, unique=True, nullable=False, index=True)
    public_title = Column(String, nullable=False)
    public_bio = Column(Text, nullable=True)
    consultation_price = Column(String, nullable=True)
    currency_code = Column(String, default="USD")
    province = Column(String, nullable=True)
    city = Column(String, nullable=True)
    sector = Column(String, nullable=True)
    address_reference = Column(Text, nullable=True)
    years_experience = Column(Integer, nullable=True)
    languages_json = Column(String, nullable=True)
    is_public = Column(Boolean, default=False)
    searchable_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")

class ProfessionalAvailability(Base):
    __tablename__ = "professional_availabilities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    professional_id = Column(String, nullable=False, index=True)
    weekday = Column(Integer, nullable=False)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)
    slot_minutes = Column(Integer, nullable=False)
    modality_code = Column(String, nullable=False)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")

class ProfessionalTimeBlock(Base):
    __tablename__ = "professional_time_blocks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    professional_id = Column(String, nullable=False, index=True)
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime, nullable=False)
    reason = Column(String, nullable=True)
    block_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")

class AppointmentStatus(str):
    PENDING_CONFIRMATION = "pending_confirmation"
    CONFIRMED = "confirmed"
    CANCELLED_BY_PATIENT = "cancelled_by_patient"
    CANCELLED_BY_PROFESSIONAL = "cancelled_by_professional"
    COMPLETED = "completed"
    NO_SHOW_PATIENT = "no_show_patient"
    NO_SHOW_PROFESSIONAL = "no_show_professional"

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    public_code = Column(String, unique=True, nullable=False, index=True)
    patient_id = Column(String, nullable=False, index=True)
    professional_id = Column(String, nullable=False, index=True)
    modality_code = Column(String, nullable=False)
    scheduled_start = Column(DateTime, nullable=False)
    scheduled_end = Column(DateTime, nullable=False)
    timezone = Column(String, default="America/Guayaquil")
    status = Column(String, nullable=False, index=True)
    patient_note = Column(String(500), nullable=True)
    admin_note = Column(String(500), nullable=True)
    cancellation_reason = Column(String(300), nullable=True)
    reschedule_reason = Column(String(300), nullable=True)
    created_from = Column(String, default="patient_app")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")

class AppointmentStatusHistory(Base):
    __tablename__ = "appointment_status_history"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    appointment_id = Column(String, nullable=False, index=True)
    old_status = Column(String, nullable=True)
    new_status = Column(String, nullable=False)
    changed_by_user_id = Column(String, nullable=True)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ProfessionalSearchImpression(Base):
    __tablename__ = "professional_search_impressions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    professional_id = Column(String, nullable=False, index=True)
    viewer_user_id = Column(String, nullable=True)
    search_session_id = Column(String, nullable=True)
    position = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)