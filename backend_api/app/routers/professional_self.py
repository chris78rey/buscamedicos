import json
import uuid
from datetime import datetime, time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.audit import AuditEvent, Severity
from app.models.professional import Professional
from app.models.step2_models import (
    Appointment,
    ProfessionalAvailability,
    ProfessionalModality,
    ProfessionalPublicProfile,
    ProfessionalSpecialty,
    ProfessionalTimeBlock,
    ServiceModality,
)
from app.models.user import User

router = APIRouter()

VALID_SLOT_MINUTES = {15, 20, 30, 45, 60}
DEFAULT_MODALITY_CODES = {"in_person_consultorio", "teleconsulta"}


class ProfessionalPublicProfilePayload(BaseModel):
    public_title: str = Field(..., min_length=3, max_length=120)
    public_bio: Optional[str] = Field(default=None, max_length=3000)
    consultation_price: Optional[float] = Field(default=None, ge=0, le=10000)
    province: Optional[str] = Field(default=None, max_length=120)
    city: Optional[str] = Field(default=None, max_length=120)
    sector: Optional[str] = Field(default=None, max_length=120)
    years_experience: Optional[int] = Field(default=None, ge=0, le=80)
    languages_json: Optional[str] = Field(default=None, max_length=600)
    is_public: bool = False


class AvailabilityPayload(BaseModel):
    weekday: int = Field(..., ge=0, le=6)
    start_time: str = Field(..., min_length=5, max_length=8)
    end_time: str = Field(..., min_length=5, max_length=8)
    slot_minutes: int
    modality_code: str = Field(..., min_length=2, max_length=80)


class TimeBlockPayload(BaseModel):
    starts_at: datetime
    ends_at: datetime
    reason: Optional[str] = Field(default=None, max_length=300)
    block_type: str = Field(default="manual_block", min_length=2, max_length=80)


def _normalize_hms(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="Time value is required")

    parts = raw.split(":")
    if len(parts) == 2:
        hh, mm = parts
        ss = "00"
    elif len(parts) == 3:
        hh, mm, ss = parts
    else:
        raise HTTPException(status_code=400, detail="Time must use HH:MM or HH:MM:SS format")

    try:
        hh_i = int(hh)
        mm_i = int(mm)
        ss_i = int(ss)
        parsed = time(hh_i, mm_i, ss_i)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid time value: {raw}") from exc

    return parsed.strftime("%H:%M:%S")


def _parse_hms(value: str) -> time:
    return time.fromisoformat(_normalize_hms(value))


def _ranges_overlap(start_a: time, end_a: time, start_b: time, end_b: time) -> bool:
    return start_a < end_b and start_b < end_a


def _serialize_json(value: Any) -> Optional[str]:
    if value is None:
        return None
    return json.dumps(value, default=str, ensure_ascii=False)


async def _get_professional_or_404(db: AsyncSession, user_id: str) -> Professional:
    result = await db.execute(
        select(Professional).where(Professional.user_id == user_id)
    )
    professional = result.scalar_one_or_none()
    if not professional:
        raise HTTPException(status_code=404, detail="Professional not found")
    return professional


async def _log_professional_audit(
    db: AsyncSession,
    current_user: User,
    action: str,
    resource_type: str,
    resource_id: str,
    metadata: Optional[Dict[str, Any]] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    event = AuditEvent(
        id=str(uuid.uuid4()),
        actor_user_id=str(current_user.id),
        actor_role_code="professional",
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        severity=Severity.INFO,
        metadata_json=_serialize_json(metadata),
        details_json=_serialize_json(details),
        created_at=datetime.utcnow(),
    )
    db.add(event)
    await db.flush()


async def _resolve_allowed_modality_codes(
    db: AsyncSession,
    professional_id: str,
) -> List[str]:
    result = await db.execute(
        select(ServiceModality.code)
        .join(
            ProfessionalModality,
            ProfessionalModality.modality_id == ServiceModality.id,
        )
        .where(
            ProfessionalModality.professional_id == professional_id,
            ProfessionalModality.deleted_at.is_(None),
            ServiceModality.is_active == True,
        )
    )
    rows = [str(row[0]) for row in result.all()]

    if rows:
        return sorted(set(rows))

    catalog_result = await db.execute(
        select(ServiceModality.code).where(ServiceModality.is_active == True)
    )
    catalog_rows = [str(row[0]) for row in catalog_result.all()]
    if catalog_rows:
        return sorted(set(catalog_rows))

    return sorted(DEFAULT_MODALITY_CODES)


async def _ensure_modality_allowed(
    db: AsyncSession,
    professional_id: str,
    modality_code: str,
) -> None:
    allowed_codes = await _resolve_allowed_modality_codes(db, professional_id)
    if modality_code not in allowed_codes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid modality_code '{modality_code}' for this professional",
        )


async def _validate_availability_payload(
    db: AsyncSession,
    professional_id: str,
    payload: AvailabilityPayload,
    exclude_id: Optional[str] = None,
) -> Dict[str, Any]:
    start_time_normalized = _normalize_hms(payload.start_time)
    end_time_normalized = _normalize_hms(payload.end_time)

    start_parsed = _parse_hms(start_time_normalized)
    end_parsed = _parse_hms(end_time_normalized)

    if start_parsed >= end_parsed:
        raise HTTPException(status_code=400, detail="start_time must be earlier than end_time")

    if payload.slot_minutes not in VALID_SLOT_MINUTES:
        raise HTTPException(
            status_code=400,
            detail="slot_minutes must be one of: 15, 20, 30, 45, 60",
        )

    await _ensure_modality_allowed(db, professional_id, payload.modality_code)

    existing_result = await db.execute(
        select(ProfessionalAvailability).where(
            ProfessionalAvailability.professional_id == professional_id,
            ProfessionalAvailability.weekday == payload.weekday,
            ProfessionalAvailability.modality_code == payload.modality_code,
            ProfessionalAvailability.deleted_at.is_(None),
        )
    )
    existing_rows = existing_result.scalars().all()

    for row in existing_rows:
        if exclude_id and str(row.id) == str(exclude_id):
            continue

        row_start = _parse_hms(row.start_time)
        row_end = _parse_hms(row.end_time)

        if _ranges_overlap(start_parsed, end_parsed, row_start, row_end):
            raise HTTPException(
                status_code=409,
                detail="Availability overlaps with another active availability for the same weekday and modality",
            )

    return {
        "start_time": start_time_normalized,
        "end_time": end_time_normalized,
    }


def _serialize_profile(professional: Professional, profile: Optional[ProfessionalPublicProfile]) -> Dict[str, Any]:
    if not profile:
        return {
            "professional_id": str(professional.id),
            "public_display_name": professional.public_display_name,
            "public_title": "",
            "public_bio": "",
            "consultation_price": None,
            "province": "",
            "city": "",
            "sector": "",
            "years_experience": None,
            "languages_json": "",
            "is_public": False,
            "professional_status": professional.status,
            "onboarding_status": professional.onboarding_status,
        }

    return {
        "id": str(profile.id),
        "professional_id": str(profile.professional_id),
        "public_display_name": professional.public_display_name,
        "public_title": profile.public_title,
        "public_bio": profile.public_bio,
        "consultation_price": float(profile.consultation_price) if profile.consultation_price not in (None, "") else None,
        "province": profile.province,
        "city": profile.city,
        "sector": profile.sector,
        "years_experience": profile.years_experience,
        "languages_json": profile.languages_json,
        "is_public": bool(profile.is_public),
        "professional_status": professional.status,
        "onboarding_status": professional.onboarding_status,
        "created_at": profile.created_at.isoformat() if profile.created_at else None,
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
    }


def _serialize_availability(item: ProfessionalAvailability) -> Dict[str, Any]:
    return {
        "id": str(item.id),
        "professional_id": str(item.professional_id),
        "weekday": item.weekday,
        "start_time": item.start_time,
        "end_time": item.end_time,
        "slot_minutes": item.slot_minutes,
        "modality_code": item.modality_code,
        "status": item.status,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


def _serialize_time_block(item: ProfessionalTimeBlock) -> Dict[str, Any]:
    return {
        "id": str(item.id),
        "professional_id": str(item.professional_id),
        "starts_at": item.starts_at.isoformat() if item.starts_at else None,
        "ends_at": item.ends_at.isoformat() if item.ends_at else None,
        "reason": item.reason,
        "block_type": item.block_type,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


@router.get("/me/public-profile")
async def get_my_public_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    professional = await _get_professional_or_404(db, str(current_user.id))

    profile_result = await db.execute(
        select(ProfessionalPublicProfile).where(
            ProfessionalPublicProfile.professional_id == professional.id
        )
    )
    profile = profile_result.scalar_one_or_none()

    return _serialize_profile(professional, profile)


@router.put("/me/public-profile")
async def update_my_public_profile(
    data: ProfessionalPublicProfilePayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    professional = await _get_professional_or_404(db, str(current_user.id))

    profile_result = await db.execute(
        select(ProfessionalPublicProfile).where(
            ProfessionalPublicProfile.professional_id == professional.id
        )
    )
    profile = profile_result.scalar_one_or_none()

    if not profile:
        profile = ProfessionalPublicProfile(
            professional_id=professional.id,
            public_title=data.public_title,
        )
        db.add(profile)
        await db.flush()

    profile.public_title = data.public_title
    profile.public_bio = data.public_bio
    profile.consultation_price = (
        f"{data.consultation_price:.2f}" if data.consultation_price is not None else None
    )
    profile.province = data.province
    profile.city = data.city
    profile.sector = data.sector
    profile.years_experience = data.years_experience
    profile.languages_json = data.languages_json
    profile.is_public = data.is_public
    profile.updated_at = datetime.utcnow()

    await _log_professional_audit(
        db=db,
        current_user=current_user,
        action="professional_public_profile_updated",
        resource_type="professional_public_profile",
        resource_id=str(profile.id),
        metadata={
            "professional_id": str(professional.id),
            "is_public": data.is_public,
        },
        details=data.model_dump(),
    )

    await db.commit()
    await db.refresh(profile)

    return _serialize_profile(professional, profile)


@router.get("/me/specialties")
async def get_my_specialties(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    professional = await _get_professional_or_404(db, str(current_user.id))

    result = await db.execute(
        select(ProfessionalSpecialty).where(
            ProfessionalSpecialty.professional_id == professional.id,
            ProfessionalSpecialty.deleted_at.is_(None),
        )
    )
    items = result.scalars().all()

    return [
        {
            "id": str(item.id),
            "professional_id": str(item.professional_id),
            "specialty_id": str(item.specialty_id),
            "is_primary": bool(item.is_primary),
        }
        for item in items
    ]


@router.get("/me/modalities")
async def get_my_modalities(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    professional = await _get_professional_or_404(db, str(current_user.id))

    result = await db.execute(
        select(ServiceModality.id, ServiceModality.code, ServiceModality.name)
        .join(
            ProfessionalModality,
            ProfessionalModality.modality_id == ServiceModality.id,
        )
        .where(
            ProfessionalModality.professional_id == professional.id,
            ProfessionalModality.deleted_at.is_(None),
            ServiceModality.is_active == True,
        )
    )
    rows = result.all()

    if rows:
        return [
            {
                "id": str(row[0]),
                "code": str(row[1]),
                "name": str(row[2]),
            }
            for row in rows
        ]

    fallback_result = await db.execute(
        select(ServiceModality.id, ServiceModality.code, ServiceModality.name).where(
            ServiceModality.is_active == True
        )
    )
    fallback_rows = fallback_result.all()
    if fallback_rows:
        return [
            {
                "id": str(row[0]),
                "code": str(row[1]),
                "name": str(row[2]),
            }
            for row in fallback_rows
        ]

    return [
        {"id": "fallback-in-person", "code": "in_person_consultorio", "name": "Consulta presencial"},
        {"id": "fallback-tele", "code": "teleconsulta", "name": "Teleconsulta"},
    ]


@router.get("/me/availabilities")
async def get_my_availabilities(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    professional = await _get_professional_or_404(db, str(current_user.id))

    result = await db.execute(
        select(ProfessionalAvailability)
        .where(
            ProfessionalAvailability.professional_id == professional.id,
            ProfessionalAvailability.deleted_at.is_(None),
        )
        .order_by(
            ProfessionalAvailability.weekday.asc(),
            ProfessionalAvailability.start_time.asc(),
        )
    )
    items = result.scalars().all()
    return [_serialize_availability(item) for item in items]


@router.post("/me/availabilities")
async def create_availability(
    data: AvailabilityPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    professional = await _get_professional_or_404(db, str(current_user.id))
    normalized = await _validate_availability_payload(db, str(professional.id), data)

    item = ProfessionalAvailability(
        professional_id=professional.id,
        weekday=data.weekday,
        start_time=normalized["start_time"],
        end_time=normalized["end_time"],
        slot_minutes=data.slot_minutes,
        modality_code=data.modality_code,
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(item)
    await db.flush()

    await _log_professional_audit(
        db=db,
        current_user=current_user,
        action="professional_availability_created",
        resource_type="professional_availability",
        resource_id=str(item.id),
        metadata={"professional_id": str(professional.id)},
        details=_serialize_availability(item),
    )

    await db.commit()
    await db.refresh(item)

    return _serialize_availability(item)


@router.put("/me/availabilities/{availability_id}")
async def update_availability(
    availability_id: str,
    data: AvailabilityPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    professional = await _get_professional_or_404(db, str(current_user.id))

    result = await db.execute(
        select(ProfessionalAvailability).where(
            ProfessionalAvailability.id == availability_id,
            ProfessionalAvailability.professional_id == professional.id,
            ProfessionalAvailability.deleted_at.is_(None),
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Availability not found")

    normalized = await _validate_availability_payload(
        db,
        str(professional.id),
        data,
        exclude_id=availability_id,
    )

    item.weekday = data.weekday
    item.start_time = normalized["start_time"]
    item.end_time = normalized["end_time"]
    item.slot_minutes = data.slot_minutes
    item.modality_code = data.modality_code
    item.status = "active"
    item.updated_at = datetime.utcnow()

    await _log_professional_audit(
        db=db,
        current_user=current_user,
        action="professional_availability_updated",
        resource_type="professional_availability",
        resource_id=str(item.id),
        metadata={"professional_id": str(professional.id)},
        details=_serialize_availability(item),
    )

    await db.commit()
    await db.refresh(item)

    return _serialize_availability(item)


@router.delete("/me/availabilities/{availability_id}")
async def delete_availability(
    availability_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    professional = await _get_professional_or_404(db, str(current_user.id))

    result = await db.execute(
        select(ProfessionalAvailability).where(
            ProfessionalAvailability.id == availability_id,
            ProfessionalAvailability.professional_id == professional.id,
            ProfessionalAvailability.deleted_at.is_(None),
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Availability not found")

    item.deleted_at = datetime.utcnow()
    item.updated_at = datetime.utcnow()

    await _log_professional_audit(
        db=db,
        current_user=current_user,
        action="professional_availability_deleted",
        resource_type="professional_availability",
        resource_id=str(item.id),
        metadata={"professional_id": str(professional.id)},
        details={"deleted_at": item.deleted_at.isoformat()},
    )

    await db.commit()
    return {"status": "deleted", "id": availability_id}


@router.get("/me/time-blocks")
async def get_my_time_blocks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    professional = await _get_professional_or_404(db, str(current_user.id))

    result = await db.execute(
        select(ProfessionalTimeBlock)
        .where(
            ProfessionalTimeBlock.professional_id == professional.id,
            ProfessionalTimeBlock.deleted_at.is_(None),
        )
        .order_by(ProfessionalTimeBlock.starts_at.desc())
    )
    items = result.scalars().all()
    return [_serialize_time_block(item) for item in items]


@router.post("/me/time-blocks")
async def create_time_block(
    data: TimeBlockPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    professional = await _get_professional_or_404(db, str(current_user.id))

    if data.starts_at >= data.ends_at:
        raise HTTPException(status_code=400, detail="starts_at must be earlier than ends_at")

    item = ProfessionalTimeBlock(
        professional_id=professional.id,
        starts_at=data.starts_at,
        ends_at=data.ends_at,
        reason=data.reason,
        block_type=data.block_type,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(item)
    await db.flush()

    await _log_professional_audit(
        db=db,
        current_user=current_user,
        action="professional_time_block_created",
        resource_type="professional_time_block",
        resource_id=str(item.id),
        metadata={"professional_id": str(professional.id)},
        details=_serialize_time_block(item),
    )

    await db.commit()
    await db.refresh(item)

    return _serialize_time_block(item)


@router.put("/me/time-blocks/{block_id}")
async def update_time_block(
    block_id: str,
    data: TimeBlockPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    professional = await _get_professional_or_404(db, str(current_user.id))

    result = await db.execute(
        select(ProfessionalTimeBlock).where(
            ProfessionalTimeBlock.id == block_id,
            ProfessionalTimeBlock.professional_id == professional.id,
            ProfessionalTimeBlock.deleted_at.is_(None),
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Time block not found")

    if data.starts_at >= data.ends_at:
        raise HTTPException(status_code=400, detail="starts_at must be earlier than ends_at")

    item.starts_at = data.starts_at
    item.ends_at = data.ends_at
    item.reason = data.reason
    item.block_type = data.block_type
    item.updated_at = datetime.utcnow()

    await _log_professional_audit(
        db=db,
        current_user=current_user,
        action="professional_time_block_updated",
        resource_type="professional_time_block",
        resource_id=str(item.id),
        metadata={"professional_id": str(professional.id)},
        details=_serialize_time_block(item),
    )

    await db.commit()
    await db.refresh(item)

    return _serialize_time_block(item)


@router.delete("/me/time-blocks/{block_id}")
async def delete_time_block(
    block_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    professional = await _get_professional_or_404(db, str(current_user.id))

    result = await db.execute(
        select(ProfessionalTimeBlock).where(
            ProfessionalTimeBlock.id == block_id,
            ProfessionalTimeBlock.professional_id == professional.id,
            ProfessionalTimeBlock.deleted_at.is_(None),
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Time block not found")

    item.deleted_at = datetime.utcnow()
    item.updated_at = datetime.utcnow()

    await _log_professional_audit(
        db=db,
        current_user=current_user,
        action="professional_time_block_deleted",
        resource_type="professional_time_block",
        resource_id=str(item.id),
        metadata={"professional_id": str(professional.id)},
        details={"deleted_at": item.deleted_at.isoformat()},
    )

    await db.commit()
    return {"status": "deleted", "id": block_id}


@router.get("/me/appointments")
async def get_my_appointments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    professional = await _get_professional_or_404(db, str(current_user.id))

    result = await db.execute(
        select(Appointment)
        .where(
            Appointment.professional_id == professional.id,
            Appointment.deleted_at.is_(None),
        )
        .order_by(Appointment.scheduled_start.desc())
    )
    items = result.scalars().all()

    return [
        {
            "id": str(item.id),
            "public_code": item.public_code,
            "patient_id": str(item.patient_id),
            "professional_id": str(item.professional_id),
            "modality_code": item.modality_code,
            "scheduled_start": item.scheduled_start.isoformat() if item.scheduled_start else None,
            "scheduled_end": item.scheduled_end.isoformat() if item.scheduled_end else None,
            "timezone": item.timezone,
            "status": item.status,
            "patient_note": item.patient_note,
            "admin_note": item.admin_note,
            "cancellation_reason": item.cancellation_reason,
            "reschedule_reason": item.reschedule_reason,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
        }
        for item in items
    ]