from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.patient import Patient
from app.models.person import Person

router = APIRouter()

class PatientResponse(BaseModel):
    id: str
    verification_level: str
    status: str
    
    class Config:
        from_attributes = True

class PatientDetailResponse(PatientResponse):
    person: dict
    
@router.get("/me", response_model=PatientDetailResponse)
async def get_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Patient).where(Patient.user_id == current_user.id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    person_result = await db.execute(select(Person).where(Person.id == patient.person_id))
    person = person_result.scalar_one_or_none()
    
    return PatientDetailResponse(
        id=patient.id,
        verification_level=patient.verification_level.value,
        status=patient.status.value,
        person={"first_name": person.first_name, "last_name": person.last_name} if person else None
    )

@router.patch("/me")
async def update_me(data: dict, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Patient).where(Patient.user_id == current_user.id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    for key, value in data.items():
        if hasattr(patient, key) and key not in ["id", "user_id", "person_id"]:
            setattr(patient, key, value)
    
    await db.commit()
    return patient