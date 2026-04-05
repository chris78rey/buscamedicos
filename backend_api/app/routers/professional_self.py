from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.models.professional import Professional, OnboardingStatus, ProfessionalStatus
from app.models.step2_models import (
    ProfessionalPublicProfile, ProfessionalAvailability, ProfessionalTimeBlock,
    Appointment, ProfessionalSpecialty, ServiceModality, ProfessionalModality
)
from app.schemas.step2_schemas import (
    PublicProfileUpdate, AvailabilityCreate, TimeBlockCreate
)
from app.services.step2_services import AppointmentService

router = APIRouter()

@router.get("/me/public-profile")
async def get_my_public_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Professional).where(Professional.user_id == current_user.id))
    prof = result.scalar_one_or_none()
    if not prof:
        raise HTTPException(status_code=404, detail="Professional not found")
    
    profile_result = await db.execute(
        select(ProfessionalPublicProfile).where(ProfessionalPublicProfile.professional_id == prof.id)
    )
    profile = profile_result.scalar_one_or_none()
    return profile or {}

@router.put("/me/public-profile")
async def update_my_public_profile(
    data: PublicProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Professional).where(Professional.user_id == current_user.id))
    prof = result.scalar_one_or_none()
    if not prof:
        raise HTTPException(status_code=404, detail="Professional not found")
    
    profile_result = await db.execute(
        select(ProfessionalPublicProfile).where(ProfessionalPublicProfile.professional_id == prof.id)
    )
    profile = profile_result.scalar_one_or_none()
    
    if not profile:
        profile = ProfessionalPublicProfile(professional_id=prof.id)
        db.add(profile)
    
    for key, value in data.model_dump(exclude_unset=True).items():
        if hasattr(profile, key) and key not in ["id", "professional_id"]:
            setattr(profile, key, value)
    
    await db.commit()
    return profile

@router.get("/me/specialties")
async def get_my_specialties(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Professional).where(Professional.user_id == current_user.id))
    prof = result.scalar_one_or_none()
    if not prof:
        raise HTTPException(status_code=404, detail="Professional not found")
    
    spec_result = await db.execute(
        select(ProfessionalSpecialty).where(
            ProfessionalSpecialty.professional_id == prof.id,
            ProfessionalSpecialty.deleted_at.is_(None)
        )
    )
    return spec_result.scalars().all()

@router.get("/me/modalities")
async def get_my_modalities(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Professional).where(Professional.user_id == current_user.id))
    prof = result.scalar_one_or_none()
    if not prof:
        raise HTTPException(status_code=404, detail="Professional not found")
    
    mod_result = await db.execute(
        select(ProfessionalModality).where(
            ProfessionalModality.professional_id == prof.id,
            ProfessionalModality.deleted_at.is_(None)
        )
    )
    return mod_result.scalars().all()

@router.get("/me/availabilities")
async def get_my_availabilities(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Professional).where(Professional.user_id == current_user.id))
    prof = result.scalar_one_or_none()
    if not prof:
        raise HTTPException(status_code=404, detail="Professional not found")
    
    avail_result = await db.execute(
        select(ProfessionalAvailability).where(
            ProfessionalAvailability.professional_id == prof.id,
            ProfessionalAvailability.deleted_at.is_(None)
        )
    )
    return avail_result.scalars().all()

@router.post("/me/availabilities")
async def create_availability(
    data: AvailabilityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Professional).where(Professional.user_id == current_user.id))
    prof = result.scalar_one_or_none()
    if not prof:
        raise HTTPException(status_code=404, detail="Professional not found")
    
    avail = ProfessionalAvailability(
        professional_id=prof.id,
        weekday=data.weekday,
        start_time=data.start_time,
        end_time=data.end_time,
        slot_minutes=data.slot_minutes,
        modality_code=data.modality_code
    )
    db.add(avail)
    await db.commit()
    return avail

@router.delete("/me/availabilities/{availability_id}")
async def delete_availability(
    availability_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Professional).where(Professional.user_id == current_user.id))
    prof = result.scalar_one_or_none()
    if not prof:
        raise HTTPException(status_code=404, detail="Professional not found")
    
    avail_result = await db.execute(
        select(ProfessionalAvailability).where(
            ProfessionalAvailability.id == availability_id,
            ProfessionalAvailability.professional_id == prof.id
        )
    )
    avail = avail_result.scalar_one_or_none()
    if not avail:
        raise HTTPException(status_code=404, detail="Availability not found")
    
    avail.deleted_at = datetime.utcnow()
    await db.commit()
    return {"status": "deleted"}

@router.get("/me/time-blocks")
async def get_my_time_blocks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Professional).where(Professional.user_id == current_user.id))
    prof = result.scalar_one_or_none()
    if not prof:
        raise HTTPException(status_code=404, detail="Professional not found")
    
    blocks_result = await db.execute(
        select(ProfessionalTimeBlock).where(
            ProfessionalTimeBlock.professional_id == prof.id,
            ProfessionalTimeBlock.deleted_at.is_(None)
        )
    )
    return blocks_result.scalars().all()

@router.post("/me/time-blocks")
async def create_time_block(
    data: TimeBlockCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Professional).where(Professional.user_id == current_user.id))
    prof = result.scalar_one_or_none()
    if not prof:
        raise HTTPException(status_code=404, detail="Professional not found")
    
    block = ProfessionalTimeBlock(
        professional_id=prof.id,
        starts_at=data.starts_at,
        ends_at=data.ends_at,
        reason=data.reason,
        block_type=data.block_type
    )
    db.add(block)
    await db.commit()
    return block

@router.delete("/me/time-blocks/{block_id}")
async def delete_time_block(
    block_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Professional).where(Professional.user_id == current_user.id))
    prof = result.scalar_one_or_none()
    if not prof:
        raise HTTPException(status_code=404, detail="Professional not found")
    
    block_result = await db.execute(
        select(ProfessionalTimeBlock).where(
            ProfessionalTimeBlock.id == block_id,
            ProfessionalTimeBlock.professional_id == prof.id
        )
    )
    block = block_result.scalar_one_or_none()
    if not block:
        raise HTTPException(status_code=404, detail="Time block not found")
    
    block.deleted_at = datetime.utcnow()
    await db.commit()
    return {"status": "deleted"}

@router.get("/me/appointments")
async def get_my_appointments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Professional).where(Professional.user_id == current_user.id))
    prof = result.scalar_one_or_none()
    if not prof:
        raise HTTPException(status_code=404, detail="Professional not found")
    
    apt_result = await db.execute(
        select(Appointment).where(
            Appointment.professional_id == prof.id,
            Appointment.deleted_at.is_(None)
        ).order_by(Appointment.scheduled_start.desc())
    )
    return apt_result.scalars().all()

@router.post("/me/appointments/{appointment_id}/confirm")
async def confirm_appointment(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Professional).where(Professional.user_id == current_user.id))
    prof = result.scalar_one_or_none()
    if not prof:
        raise HTTPException(status_code=404, detail="Professional not found")
    
    try:
        apt = await AppointmentService.transition_appointment(db, appointment_id, "confirmed", current_user.id)
        return apt
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/me/appointments/{appointment_id}/cancel")
async def cancel_appointment(
    appointment_id: str,
    reason: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Professional).where(Professional.user_id == current_user.id))
    prof = result.scalar_one_or_none()
    if not prof:
        raise HTTPException(status_code=404, detail="Professional not found")
    
    try:
        apt = await AppointmentService.transition_appointment(db, appointment_id, "cancelled_by_professional", current_user.id, reason)
        return apt
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/me/appointments/{appointment_id}/complete")
async def complete_appointment(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Professional).where(Professional.user_id == current_user.id))
    prof = result.scalar_one_or_none()
    if not prof:
        raise HTTPException(status_code=404, detail="Professional not found")
    
    try:
        apt = await AppointmentService.transition_appointment(db, appointment_id, "completed", current_user.id)
        return apt
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))