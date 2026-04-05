from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SpecialtyResponse(BaseModel):
    id: str
    code: str
    name: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True

class PublicProfessionalSearchParams(BaseModel):
    specialty: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    modality: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    available_date: Optional[str] = None

class PublicProfessionalResponse(BaseModel):
    professional_id: str
    public_slug: Optional[str]
    public_display_name: str
    public_title: str
    specialties: list[str]
    province: Optional[str]
    city: Optional[str]
    sector: Optional[str]
    modalities: list[str]
    years_experience: Optional[int]
    consultation_price: Optional[float]
    next_available_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class SlotResponse(BaseModel):
    start: datetime
    end: datetime
    is_available: bool

class PublicProfileUpdate(BaseModel):
    public_title: Optional[str] = None
    public_bio: Optional[str] = None
    consultation_price: Optional[float] = None
    province: Optional[str] = None
    city: Optional[str] = None
    sector: Optional[str] = None
    years_experience: Optional[int] = None
    languages_json: Optional[str] = None
    is_public: bool = False

class AvailabilityCreate(BaseModel):
    weekday: int
    start_time: str
    end_time: str
    slot_minutes: int
    modality_code: str

class TimeBlockCreate(BaseModel):
    starts_at: datetime
    ends_at: datetime
    reason: Optional[str] = None
    block_type: str = "manual"

class AppointmentCreate(BaseModel):
    professional_id: str
    modality_code: str
    scheduled_start: datetime
    patient_note: Optional[str] = None

class AppointmentResponse(BaseModel):
    id: str
    public_code: str
    status: str
    scheduled_start: datetime
    scheduled_end: datetime
    professional_id: str
    patient_id: str
    modality_code: str
    
    class Config:
        from_attributes = True

class AppointmentStateTransition(BaseModel):
    reason: Optional[str] = None