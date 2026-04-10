import json
import uuid
from datetime import datetime, time
from hashlib import sha256
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File as FastAPIFile, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.audit import AuditEvent, Severity
from app.models.file import File as StoredFile
from app.models.professional import OnboardingStatus, Professional, ProfessionalStatus
from app.models.professional_document import DocumentType, ProfessionalDocument, ReviewStatus
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
from app.models.verification import (
    VerificationEvent,
    VerificationEventType,
    VerificationRequest,
    VerificationRequestStatus,
)
from app.services.file_storage_service import FileStorageService

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


class ProfessionalUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    public_display_name: Optional[str] = Field(default=None, max_length=255)
    professional_type: Optional[str] = Field(default=None, max_length=255)
    bio_public: Optional[str] = Field(default=None, max_length=5000)
    years_experience: Optional[int] = Field(default=None, ge=0, le=80)
    languages: Optional[List[str]] = Field(default=None)
    public_slug: Optional[str] = Field(default=None, max_length=255)


class DocumentUploadResponse(BaseModel):
    id: str
    document_type: str
    file_id: str
    original_filename: str
    mime_type: str
    sha256: str
    review_status: str
    uploaded_at: datetime
    download_url: str


class DocumentResponse(BaseModel):
    id: str
    professional_id: str
    document_type: str
    file_id: str
    original_filename: str
    mime_type: str
    sha256: str
    review_status: str
    review_notes: Optional[str]
    uploaded_at: datetime
    download_url: str


class SubmitVerificationResponse(BaseModel):
    id: str
    status: str
    submitted_at: datetime


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
        select(Professional).where(
            Professional.user_id == user_id,
            Professional.deleted_at.is_(None)
        )
    )
    professional = result.scalar_one_or_none()
    if not professional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Su cuenta no tiene un perfil profesional asociado o el perfil fue eliminado."
        )
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
        entity_type=resource_type,
        entity_id=resource_id,
        severity=Severity.INFO,
        before_json=_serialize_json(metadata),
        after_json=_serialize_json(details),
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
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cruce de horario detectado con otra disponibilidad ({row.start_time} - {row.end_time}, modalidad: {row.modality_code})",
            )

    return {
        "start_time": start_time_normalized,
        "end_time": end_time_normalized,
    }


async def _validate_time_block_payload(
    db: AsyncSession,
    professional_id: str,
    payload: TimeBlockPayload,
    exclude_id: Optional[str] = None,
) -> None:
    if payload.starts_at >= payload.ends_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha/hora de inicio debe ser anterior a la de fin."
        )

    # Check for overlaps with other time blocks
    existing_result = await db.execute(
        select(ProfessionalTimeBlock).where(
            ProfessionalTimeBlock.professional_id == professional_id,
            ProfessionalTimeBlock.deleted_at.is_(None),
            ProfessionalTimeBlock.ends_at > payload.starts_at,
            ProfessionalTimeBlock.starts_at < payload.ends_at,
        )
    )
    existing_rows = existing_result.scalars().all()

    for row in existing_rows:
        if exclude_id and str(row.id) == str(exclude_id):
            continue
        
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un bloqueo en este rango ({row.starts_at} a {row.ends_at})."
        )


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


def _download_url(file_id: str) -> str:
    return f"/api/v1/files/{file_id}/download"


def _serialize_professional_self(professional: Professional) -> Dict[str, Any]:
    languages = []
    if professional.languages_json:
        try:
            languages = json.loads(professional.languages_json)
        except:
            languages = []
            
    return {
        "id": str(professional.id),
        "user_id": str(professional.user_id),
        "person_id": str(professional.person_id),
        "public_display_name": professional.public_display_name,
        "professional_type": professional.professional_type,
        "bio_public": professional.bio_public,
        "years_experience": int(professional.years_experience) if professional.years_experience and professional.years_experience.isdigit() else 0,
        "languages": languages,
        "public_slug": professional.public_slug,
        "onboarding_status": professional.onboarding_status.value if professional.onboarding_status else None,
        "status": professional.status.value if professional.status else None,
        "is_public_profile_enabled": bool(professional.is_public_profile_enabled),
        "created_at": professional.created_at,
        "updated_at": professional.updated_at,
    }


def _serialize_document(item: ProfessionalDocument) -> Dict[str, Any]:
    return {
        "id": str(item.id),
        "professional_id": str(item.professional_id),
        "document_type": item.document_type.value if item.document_type else None,
        "file_id": str(item.file_id),
        "original_filename": item.original_filename,
        "mime_type": item.mime_type,
        "sha256": item.sha256,
        "review_status": item.review_status.value if item.review_status else None,
        "review_notes": item.review_notes,
        "uploaded_at": item.uploaded_at,
        "download_url": _download_url(str(item.file_id)),
    }


async def _get_document_or_404(
    db: AsyncSession,
    professional_id: str,
    document_id: str,
) -> ProfessionalDocument:
    result = await db.execute(
        select(ProfessionalDocument).where(
            ProfessionalDocument.id == document_id,
            ProfessionalDocument.professional_id == professional_id,
            ProfessionalDocument.deleted_at.is_(None),
        )
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


async def _get_file_for_document(
    db: AsyncSession,
    *,
    file_id: str,
) -> Optional[StoredFile]:
    result = await db.execute(
        select(StoredFile).where(
            StoredFile.id == file_id,
        )
    )
    return result.scalar_one_or_none()


async def _soft_delete_document_and_file(
    *,
    db: AsyncSession,
    file_storage: FileStorageService,
    document: ProfessionalDocument,
    current_user: User,
    file_record: Optional[StoredFile] = None,
) -> Optional[StoredFile]:
    now = datetime.utcnow()
    document.deleted_at = now
    document.deleted_by = str(current_user.id)
    document.updated_at = now

    resolved_file = file_record or await _get_file_for_document(
        db,
        file_id=str(document.file_id),
    )

    if resolved_file and not resolved_file.deleted_at:
        resolved_file.deleted_at = now
        resolved_file.deleted_by = str(current_user.id)
        resolved_file.relative_path = file_storage.soft_delete_file(resolved_file.relative_path)

    return resolved_file


async def _create_professional_document(
    *,
    db: AsyncSession,
    professional: Professional,
    current_user: User,
    document_type: DocumentType,
    upload: UploadFile,
) -> ProfessionalDocument:
    storage = FileStorageService()
    force_pdf = (document_type == DocumentType.DEGREE)
    
    file_record, content = await storage.save_professional_document(
        upload=upload,
        professional_id=str(professional.id),
        document_type=document_type.value,
        owner_user_id=str(current_user.id),
        force_pdf=force_pdf,
    )

    db.add(file_record)
    await db.flush()

    existing_result = await db.execute(
        select(ProfessionalDocument).where(
            ProfessionalDocument.professional_id == professional.id,
            ProfessionalDocument.document_type == document_type,
            ProfessionalDocument.deleted_at.is_(None),
        )
    )
    existing_document = existing_result.scalar_one_or_none()
    if existing_document:
        existing_file = await _get_file_for_document(
            db,
            file_id=str(existing_document.file_id),
        )
        await _soft_delete_document_and_file(
            db=db,
            file_storage=storage,
            document=existing_document,
            current_user=current_user,
            file_record=existing_file,
        )

    document = ProfessionalDocument(
        professional_id=professional.id,
        document_type=document_type,
        file_id=file_record.id,
        original_filename=file_record.original_filename,
        mime_type=file_record.mime_type,
        sha256=file_record.sha256,
        uploaded_at=datetime.utcnow(),
        review_status=ReviewStatus.PENDING,
        created_by=str(current_user.id),
        updated_by=str(current_user.id),
    )
    db.add(document)
    await db.flush()
    return document


@router.get("/me")
async def get_my_professional_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    professional = await _get_professional_or_404(db, str(current_user.id))
    return _serialize_professional_self(professional)


@router.patch("/me")
async def update_my_professional_profile(
    data: ProfessionalUpdatePayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    professional = await _get_professional_or_404(db, str(current_user.id))
    before = _serialize_professional_self(professional)

    payload = data.model_dump(exclude_unset=True)
    if not payload:
        raise HTTPException(status_code=400, detail="At least one field must be provided")

    if "public_slug" in payload and payload["public_slug"]:
        slug_result = await db.execute(
            select(Professional).where(
                Professional.public_slug == payload["public_slug"],
                Professional.id != professional.id,
                Professional.deleted_at.is_(None),
            )
        )
        if slug_result.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="public_slug is already in use")

    if "languages" in payload:
        professional.languages_json = json.dumps(payload.pop("languages"))
    
    if "years_experience" in payload:
        professional.years_experience = str(payload.pop("years_experience"))

    for key, value in payload.items():
        setattr(professional, key, value)

    professional.updated_at = datetime.utcnow()
    professional.updated_by = str(current_user.id)

    await _log_professional_audit(
        db=db,
        current_user=current_user,
        action="professional_profile_updated",
        resource_type="professional",
        resource_id=str(professional.id),
        metadata=before,
        details=_serialize_professional_self(professional),
    )

    await db.commit()
    await db.refresh(professional)
    return _serialize_professional_self(professional)


@router.post("/me/documents", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_my_document(
    document_type: DocumentType = Form(...),
    file: UploadFile = FastAPIFile(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    professional = await _get_professional_or_404(db, str(current_user.id))

    try:
        document = await _create_professional_document(
            db=db,
            professional=professional,
            current_user=current_user,
            document_type=document_type,
            upload=file,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await _log_professional_audit(
        db=db,
        current_user=current_user,
        action="professional_document_uploaded",
        resource_type="professional_document",
        resource_id=str(document.id),
        metadata={
            "professional_id": str(professional.id),
            "document_type": document.document_type.value,
        },
        details=_serialize_document(document),
    )

    await db.commit()
    await db.refresh(document)

    document_data = _serialize_document(document)
    return DocumentUploadResponse(
        id=document_data["id"],
        document_type=document_data["document_type"],
        file_id=document_data["file_id"],
        original_filename=document_data["original_filename"],
        mime_type=document_data["mime_type"],
        sha256=document_data["sha256"],
        review_status=document_data["review_status"],
        uploaded_at=document_data["uploaded_at"],
        download_url=document_data["download_url"],
    )


@router.get("/me/documents", response_model=List[DocumentResponse])
async def list_my_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    professional = await _get_professional_or_404(db, str(current_user.id))

    result = await db.execute(
        select(ProfessionalDocument)
        .where(
            ProfessionalDocument.professional_id == professional.id,
            ProfessionalDocument.deleted_at.is_(None),
        )
        .order_by(ProfessionalDocument.uploaded_at.desc())
    )
    documents = result.scalars().all()
    return [DocumentResponse(**_serialize_document(document)) for document in documents]


@router.delete("/me/documents/{doc_id}")
async def delete_my_document(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    professional = await _get_professional_or_404(db, str(current_user.id))
    document = await _get_document_or_404(db, str(professional.id), doc_id)

    storage = FileStorageService()
    file_record = await _soft_delete_document_and_file(
        db=db,
        file_storage=storage,
        document=document,
        current_user=current_user,
    )

    await _log_professional_audit(
        db=db,
        current_user=current_user,
        action="professional_document_deleted",
        resource_type="professional_document",
        resource_id=str(document.id),
        metadata={
            "professional_id": str(professional.id),
            "file_id": str(document.file_id),
            "file_deleted": bool(file_record),
        },
        details={"deleted_at": document.deleted_at.isoformat() if document.deleted_at else None},
    )

    await db.commit()
    return {"status": "deleted", "id": doc_id}


@router.post("/me/submit-verification", response_model=SubmitVerificationResponse, status_code=status.HTTP_201_CREATED)
async def submit_my_verification(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    professional = await _get_professional_or_404(db, str(current_user.id))

    degree_result = await db.execute(
        select(ProfessionalDocument).where(
            ProfessionalDocument.professional_id == professional.id,
            ProfessionalDocument.document_type == DocumentType.DEGREE,
            ProfessionalDocument.deleted_at.is_(None),
        )
    )
    degree_document = degree_result.scalar_one_or_none()
    if not degree_document:
        raise HTTPException(status_code=400, detail="A degree document is required before submitting verification")

    if not (professional.public_display_name or "").strip():
        raise HTTPException(status_code=400, detail="public_display_name is required before submitting verification")

    if not (professional.professional_type or "").strip():
        raise HTTPException(status_code=400, detail="professional_type is required before submitting verification")

    existing_request_result = await db.execute(
        select(VerificationRequest).where(
            VerificationRequest.professional_id == professional.id,
            VerificationRequest.status.in_(
                [VerificationRequestStatus.SUBMITTED, VerificationRequestStatus.UNDER_REVIEW]
            ),
            VerificationRequest.deleted_at.is_(None),
        )
    )
    existing_request = existing_request_result.scalar_one_or_none()
    if existing_request:
        raise HTTPException(status_code=409, detail="There is already an active verification request")

    now = datetime.utcnow()
    verification_request = VerificationRequest(
        professional_id=professional.id,
        submitted_at=now,
        status=VerificationRequestStatus.SUBMITTED,
        created_at=now,
        updated_at=now,
        created_by=str(current_user.id),
        updated_by=str(current_user.id),
    )
    db.add(verification_request)
    await db.flush()

    verification_event = VerificationEvent(
        verification_request_id=verification_request.id,
        event_type=VerificationEventType.SUBMITTED,
        event_payload_json=_serialize_json(
            {
                "professional_id": str(professional.id),
                "document_id": str(degree_document.id),
                "submitted_at": now.isoformat(),
            }
        ),
        created_at=now,
        created_by=str(current_user.id),
    )
    db.add(verification_event)

    professional.onboarding_status = OnboardingStatus.SUBMITTED
    professional.status = ProfessionalStatus.PENDING_REVIEW
    professional.is_public_profile_enabled = False
    professional.updated_at = now
    professional.updated_by = str(current_user.id)

    await _log_professional_audit(
        db=db,
        current_user=current_user,
        action="professional_verification_submitted",
        resource_type="verification_request",
        resource_id=str(verification_request.id),
        metadata={"professional_id": str(professional.id)},
        details={
            "status": verification_request.status.value,
            "onboarding_status": professional.onboarding_status.value,
            "professional_status": professional.status.value,
        },
    )

    await db.commit()
    await db.refresh(verification_request)
    return SubmitVerificationResponse(
        id=str(verification_request.id),
        status=verification_request.status.value,
        submitted_at=verification_request.submitted_at,
    )


@router.get("/me/verification-status")
async def get_my_verification_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    professional = await _get_professional_or_404(db, str(current_user.id))

    # Get active verification request
    result = await db.execute(
        select(VerificationRequest)
        .where(
            VerificationRequest.professional_id == professional.id,
            VerificationRequest.deleted_at.is_(None),
        )
        .order_by(VerificationRequest.submitted_at.desc())
    )
    request = result.scalars().first()

    # Get documents
    docs_result = await db.execute(
        select(ProfessionalDocument)
        .where(
            ProfessionalDocument.professional_id == professional.id,
            ProfessionalDocument.deleted_at.is_(None),
        )
    )
    documents = docs_result.scalars().all()

    return {
        "professional_status": professional.status.value if professional.status else None,
        "onboarding_status": professional.onboarding_status.value if professional.onboarding_status else None,
        "request_status": request.status.value if request else None,
        "submitted_at": request.submitted_at if request else None,
        "decision_reason": request.decision_reason if request else None,
        "documents": [_serialize_document(doc) for doc in documents],
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
    await _validate_time_block_payload(db, str(professional.id), data)

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

    await _validate_time_block_payload(db, str(professional.id), data, exclude_id=block_id)

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
