from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.step2_models import Specialty, ProfessionalPublicProfile, Professional
from app.models.professional import Professional as ProfModel, OnboardingStatus, ProfessionalStatus
from app.schemas.step2_schemas import PublicProfessionalResponse, SlotResponse
from app.services.step2_services import SlotService

router = APIRouter()

@router.get("/specialties")
async def get_specialties(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Specialty).where(Specialty.is_active == True))
    return result.scalars().all()

@router.get("/professionals")
async def search_professionals(
    specialty: str = None,
    province: str = None,
    city: str = None,
    modality: str = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(ProfessionalPublicProfile).where(
        ProfessionalPublicProfile.is_public == True,
        ProfessionalPublicProfile.deleted_at.is_(None)
    )
    
    if province:
        query = query.where(ProfessionalPublicProfile.province == province)
    if city:
        query = query.where(ProfessionalPublicProfile.city == city)
    
    result = await db.execute(query)
    profiles = result.scalars().all()
    
    response = []
    for p in profiles:
        prof_result = await db.execute(select(ProfModel).where(ProfModel.id == p.professional_id))
        prof = prof_result.scalar_one_or_none()
        if not prof or prof.status != ProfessionalStatus.ACTIVE or prof.onboarding_status != OnboardingStatus.APPROVED:
            continue
        
        response.append({
            "professional_id": p.professional_id,
            "public_slug": prof.public_slug,
            "public_display_name": prof.public_display_name,
            "public_title": p.public_title,
            "specialties": [],
            "province": p.province,
            "city": p.city,
            "sector": p.sector,
            "modalities": [],
            "years_experience": p.years_experience,
            "consultation_price": float(p.consultation_price) if p.consultation_price else None,
            "next_available_at": None
        })
    
    return response

@router.get("/professionals/{identifier}")
async def get_public_professional(identifier: str, db: AsyncSession = Depends(get_db)):
    if identifier.startswith("prof_"):
        result = await db.execute(select(Professional).where(Professional.id == identifier))
    else:
        result = await db.execute(select(Professional).where(Professional.public_slug == identifier))
    
    prof = result.scalar_one_or_none()
    if not prof:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Professional not found")
    
    if prof.status != ProfessionalStatus.ACTIVE or prof.onboarding_status != OnboardingStatus.APPROVED:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Professional not publicly available")
    
    profile_result = await db.execute(
        select(ProfessionalPublicProfile).where(ProfessionalPublicProfile.professional_id == prof.id)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile or not profile.is_public:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Professional profile not public")
    
    return {
        "professional_id": prof.id,
        "public_display_name": prof.public_display_name,
        "public_title": profile.public_title,
        "public_bio": profile.public_bio,
        "specialties": [],
        "province": profile.province,
        "city": profile.city,
        "sector": profile.sector,
        "years_experience": profile.years_experience,
        "consultation_price": float(profile.consultation_price) if profile.consultation_price else None,
    }

@router.get("/professionals/{professional_id}/slots")
async def get_slots(
    professional_id: str,
    date: str = Query(..., regex="\\d{4}-\\d{2}-\\d{2}"),
    modality: str = Query(default="in_person_consultorio"),
    db: AsyncSession = Depends(get_db)
):
    slots = await SlotService.get_available_slots(db, professional_id, date, modality)
    return [{"start": s["start"].isoformat(), "end": s["end"].isoformat(), "is_available": s["is_available"]} for s in slots]