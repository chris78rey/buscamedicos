from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.audit import AuditEvent, Severity
from app.models.person import Person
from app.models.professional import OnboardingStatus, Professional, ProfessionalStatus
from app.models.professional_document import DocumentType, ProfessionalDocument, ReviewStatus
from app.models.role import RoleCode
from app.models.user import User
from app.models.verification import (
    VerificationEvent,
    VerificationEventType,
    VerificationRequest,
    VerificationRequestStatus,
)

router = APIRouter(prefix="/verification-requests", tags=["admin-verification"])


class VerificationRequestListItem(BaseModel):
    id: str
    professional_id: str
    status: str
    submitted_at: datetime
    assigned_admin_id: Optional[str]
    reviewed_by: Optional[str]
    decision_reason: Optional[str]
    professional_display_name: Optional[str]
    professional_email: Optional[str]
    document_count: int
    approved_count: int
    pending_count: int
    rejected_count: int


class ReasonPayload(BaseModel):
    reason: str


class ApprovePayload(BaseModel):
    notes: Optional[str] = None




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


class ProfessionalBasicInfo(BaseModel):
    id: str
    public_display_name: Optional[str]
    professional_type: Optional[str]
    email: Optional[str]


class PersonBasicInfo(BaseModel):
    id: str
    first_name: Optional[str]
    last_name: Optional[str]
    national_id: Optional[str]
    phone: Optional[str]


class VerificationRequestDetail(BaseModel):
    id: str
    professional_id: str
    status: str
    submitted_at: datetime
    assigned_admin_id: Optional[str]
    decision_at: Optional[datetime]
    decision_reason: Optional[str]
    reviewed_by: Optional[str]
    professional: Optional[ProfessionalBasicInfo]
    person: Optional[PersonBasicInfo]
    documents: List[DocumentResponse]


async def _get_verification_or_404(db: AsyncSession, request_id: str) -> VerificationRequest:
    result = await db.execute(
        select(VerificationRequest).where(
            VerificationRequest.id == request_id,
            VerificationRequest.deleted_at.is_(None)
        )
    )
    verification = result.scalar_one_or_none()
    if not verification:
        raise HTTPException(status_code=404, detail="Verification request not found")
    return verification


async def _get_document_or_404(db: AsyncSession, document_id: str) -> ProfessionalDocument:
    result = await db.execute(
        select(ProfessionalDocument).where(
            ProfessionalDocument.id == document_id,
            ProfessionalDocument.deleted_at.is_(None)
        )
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


async def _log_audit(
    db: AsyncSession,
    action: str,
    entity_type: str,
    entity_id: str,
    actor_user_id: str,
    severity: Severity = Severity.INFO,
    before_json: Optional[str] = None,
    after_json: Optional[str] = None,
) -> None:
    event = AuditEvent(
        id=None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_user_id=actor_user_id,
        severity=severity,
        before_json=before_json,
        after_json=after_json,
        created_at=datetime.utcnow(),
    )
    db.add(event)
    await db.flush()


async def _create_verification_event(
    db: AsyncSession,
    verification_request_id: str,
    event_type: VerificationEventType,
    payload: Optional[Dict[str, Any]] = None,
    created_by: Optional[str] = None,
) -> VerificationEvent:
    import json
    event = VerificationEvent(
        id=None,
        verification_request_id=verification_request_id,
        event_type=event_type,
        event_payload_json=json.dumps(payload) if payload else None,
        created_at=datetime.utcnow(),
        created_by=created_by,
    )
    db.add(event)
    await db.flush()
    return event


def _download_url(file_id: str) -> str:
    return f"/files/{file_id}/download"



@router.get("", response_model=List[VerificationRequestListItem])
async def list_verification_requests(
    current_user: User = Depends(require_role([RoleCode.ADMIN_VALIDATION, RoleCode.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VerificationRequest).where(VerificationRequest.deleted_at.is_(None))
    )
    requests = result.scalars().all()

    items = []
    for req in requests:
        prof_result = await db.execute(select(Professional).where(Professional.id == req.professional_id))
        professional = prof_result.scalar_one_or_none()

        user_result = await db.execute(select(User).where(User.id == professional.user_id)) if professional else None
        user = user_result.scalar_one_or_none() if user_result else None

        docs_result = await db.execute(
            select(ProfessionalDocument).where(
                ProfessionalDocument.professional_id == req.professional_id,
                ProfessionalDocument.deleted_at.is_(None)
            )
        )
        documents = docs_result.scalars().all()

        approved_count = sum(1 for d in documents if d.review_status == ReviewStatus.APPROVED)
        pending_count = sum(1 for d in documents if d.review_status == ReviewStatus.PENDING)
        rejected_count = sum(1 for d in documents if d.review_status == ReviewStatus.REJECTED)

        items.append(VerificationRequestListItem(
            id=str(req.id),
            professional_id=str(req.professional_id),
            status=req.status.value if req.status else None,
            submitted_at=req.submitted_at,
            assigned_admin_id=str(req.assigned_admin_id) if req.assigned_admin_id else None,
            reviewed_by=str(req.reviewed_by) if req.reviewed_by else None,
            decision_reason=req.decision_reason,
            professional_display_name=professional.public_display_name if professional else None,
            professional_email=user.email if user else None,
            document_count=len(documents),
            approved_count=approved_count,
            pending_count=pending_count,
            rejected_count=rejected_count,
        ))

    return items


@router.get("/{request_id}", response_model=VerificationRequestDetail)
async def get_verification_request(
    request_id: str,
    current_user: User = Depends(require_role([RoleCode.ADMIN_VALIDATION, RoleCode.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    verification = await _get_verification_or_404(db, request_id)

    prof_result = await db.execute(select(Professional).where(Professional.id == verification.professional_id))
    professional = prof_result.scalar_one_or_none()

    person = None
    if professional:
        person_result = await db.execute(select(Person).where(Person.id == professional.person_id))
        person = person_result.scalar_one_or_none()

        user_result = await db.execute(select(User).where(User.id == professional.user_id))
        user = user_result.scalar_one_or_none()

    docs_result = await db.execute(
        select(ProfessionalDocument).where(
            ProfessionalDocument.professional_id == verification.professional_id,
            ProfessionalDocument.deleted_at.is_(None)
        )
    )
    documents = docs_result.scalars().all()

    doc_responses = [
        DocumentResponse(
            id=str(doc.id),
            professional_id=str(doc.professional_id),
            document_type=doc.document_type.value if doc.document_type else None,
            file_id=str(doc.file_id),
            original_filename=doc.original_filename,
            mime_type=doc.mime_type,
            sha256=doc.sha256,
            review_status=doc.review_status.value if doc.review_status else None,
            review_notes=doc.review_notes,
            uploaded_at=doc.uploaded_at,
            download_url=_download_url(str(doc.file_id)),
        )
        for doc in documents
    ]

    prof_basic = None
    if professional:
        user_result = await db.execute(select(User).where(User.id == professional.user_id))
        user = user_result.scalar_one_or_none()
        prof_basic = ProfessionalBasicInfo(
            id=str(professional.id),
            public_display_name=professional.public_display_name,
            professional_type=professional.professional_type,
            email=user.email if user else None,
        )

    person_basic = None
    if person:
        person_basic = PersonBasicInfo(
            id=str(person.id),
            first_name=person.first_name,
            last_name=person.last_name,
            national_id=person.national_id,
            phone=person.phone,
        )

    return VerificationRequestDetail(
        id=str(verification.id),
        professional_id=str(verification.professional_id),
        status=verification.status.value if verification.status else None,
        submitted_at=verification.submitted_at,
        assigned_admin_id=str(verification.assigned_admin_id) if verification.assigned_admin_id else None,
        decision_at=verification.decision_at,
        decision_reason=verification.decision_reason,
        reviewed_by=str(verification.reviewed_by) if verification.reviewed_by else None,
        professional=prof_basic,
        person=person_basic,
        documents=doc_responses,
    )


@router.post("/{request_id}/assign")
async def assign_verification(
    request_id: str,
    current_user: User = Depends(require_role([RoleCode.ADMIN_VALIDATION, RoleCode.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    verification = await _get_verification_or_404(db, request_id)

    verification.assigned_admin_id = current_user.id
    verification.status = VerificationRequestStatus.UNDER_REVIEW

    await _create_verification_event(
        db,
        verification_request_id=request_id,
        event_type=VerificationEventType.ASSIGNED,
        payload={"admin_id": str(current_user.id)},
        created_by=str(current_user.id),
    )

    await _log_audit(
        db,
        action="admin_assign_verification",
        entity_type="verification_request",
        entity_id=request_id,
        actor_user_id=str(current_user.id),
        severity=Severity.INFO,
        after_json='{"assigned_admin_id": "' + str(current_user.id) + '", "status": "under_review"}',
    )

    await db.commit()
    return {"status": "assigned", "admin_id": str(current_user.id)}


@router.post("/{request_id}/documents/{document_id}/approve")
async def approve_document(
    request_id: str,
    document_id: str,
    payload: ApprovePayload,
    current_user: User = Depends(require_role([RoleCode.ADMIN_VALIDATION, RoleCode.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    notes = payload.notes

    verification = await _get_verification_or_404(db, request_id)

    document = await _get_document_or_404(db, document_id)

    if document.professional_id != verification.professional_id:
        raise HTTPException(status_code=400, detail="Document does not belong to this verification request")

    document.review_status = ReviewStatus.APPROVED
    document.review_notes = notes
    document.updated_at = datetime.utcnow()
    document.updated_by = str(current_user.id)

    await _create_verification_event(
        db,
        verification_request_id=request_id,
        event_type=VerificationEventType.DOCUMENT_APPROVED,
        payload={
            "document_id": str(document_id),
            "document_type": document.document_type.value if document.document_type else None,
            "notes": notes,
        },
        created_by=str(current_user.id),
    )

    await _log_audit(
        db,
        action="admin_approve_document",
        entity_type="professional_document",
        entity_id=str(document_id),
        actor_user_id=str(current_user.id),
        severity=Severity.INFO,
        after_json='{"review_status": "approved", "notes": "' + (notes or "") + '"}',
    )

    await db.commit()
    return {"status": "document_approved", "document_id": str(document_id)}


@router.post("/{request_id}/documents/{document_id}/reject")
async def reject_document(
    request_id: str,
    document_id: str,
    payload: ReasonPayload,
    current_user: User = Depends(require_role([RoleCode.ADMIN_VALIDATION, RoleCode.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    reason = payload.reason

    verification = await _get_verification_or_404(db, request_id)

    document = await _get_document_or_404(db, document_id)

    if document.professional_id != verification.professional_id:
        raise HTTPException(status_code=400, detail="Document does not belong to this verification request")

    if not reason or not reason.strip():
        raise HTTPException(status_code=400, detail="Reason is required for rejection")

    document.review_status = ReviewStatus.REJECTED
    document.review_notes = reason
    document.updated_at = datetime.utcnow()
    document.updated_by = str(current_user.id)

    await _create_verification_event(
        db,
        verification_request_id=request_id,
        event_type=VerificationEventType.DOCUMENT_REJECTED,
        payload={
            "document_id": str(document_id),
            "document_type": document.document_type.value if document.document_type else None,
            "reason": reason,
        },
        created_by=str(current_user.id),
    )

    await _log_audit(
        db,
        action="admin_reject_document",
        entity_type="professional_document",
        entity_id=str(document_id),
        actor_user_id=str(current_user.id),
        severity=Severity.WARNING,
        after_json='{"review_status": "rejected", "reason": "' + reason + '"}',
    )

    await db.commit()
    return {"status": "document_rejected", "document_id": str(document_id), "reason": reason}


@router.post("/{request_id}/request-correction")
async def request_correction(
    request_id: str,
    payload: ReasonPayload,
    current_user: User = Depends(require_role([RoleCode.ADMIN_VALIDATION, RoleCode.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    reason = payload.reason

    verification = await _get_verification_or_404(db, request_id)

    if not reason or not reason.strip():
        raise HTTPException(status_code=400, detail="Reason is required")

    verification.status = VerificationRequestStatus.NEEDS_CORRECTION

    professional_result = await db.execute(select(Professional).where(Professional.id == verification.professional_id))
    professional = professional_result.scalar_one_or_none()

    if professional:
        professional.onboarding_status = OnboardingStatus.REJECTED
        professional.status = ProfessionalStatus.REJECTED
        professional.is_public_profile_enabled = False
        professional.updated_at = datetime.utcnow()
        professional.updated_by = str(current_user.id)

    await _create_verification_event(
        db,
        verification_request_id=request_id,
        event_type=VerificationEventType.CORRECTION_REQUESTED,
        payload={"reason": reason},
        created_by=str(current_user.id),
    )

    await _log_audit(
        db,
        action="admin_request_correction",
        entity_type="verification_request",
        entity_id=request_id,
        actor_user_id=str(current_user.id),
        severity=Severity.WARNING,
        after_json='{"status": "needs_correction", "reason": "' + reason + '"}',
    )

    await db.commit()
    return {"status": "correction_requested", "reason": reason}


@router.post("/{request_id}/approve")
async def approve_verification(
    request_id: str,
    current_user: User = Depends(require_role([RoleCode.ADMIN_VALIDATION, RoleCode.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    verification = await _get_verification_or_404(db, request_id)

    docs_result = await db.execute(
        select(ProfessionalDocument).where(
            ProfessionalDocument.professional_id == verification.professional_id,
            ProfessionalDocument.document_type == DocumentType.DEGREE,
            ProfessionalDocument.deleted_at.is_(None),
        )
    )
    degree_docs = docs_result.scalars().all()

    has_approved_degree = any(d.review_status == ReviewStatus.APPROVED for d in degree_docs)

    if not has_approved_degree:
        raise HTTPException(
            status_code=400,
            detail="Cannot approve verification: No degree document has been approved yet. Please review and approve the degree document first."
        )

    verification.status = VerificationRequestStatus.APPROVED
    verification.decision_at = datetime.utcnow()
    verification.reviewed_by = str(current_user.id)

    professional_result = await db.execute(select(Professional).where(Professional.id == verification.professional_id))
    professional = professional_result.scalar_one_or_none()

    if professional:
        professional.onboarding_status = OnboardingStatus.APPROVED
        professional.status = ProfessionalStatus.ACTIVE
        professional.is_public_profile_enabled = True
        professional.updated_at = datetime.utcnow()
        professional.updated_by = str(current_user.id)

    await _create_verification_event(
        db,
        verification_request_id=request_id,
        event_type=VerificationEventType.APPROVED,
        payload={"reviewed_by": str(current_user.id)},
        created_by=str(current_user.id),
    )

    await _log_audit(
        db,
        action="admin_approve_verification",
        entity_type="verification_request",
        entity_id=request_id,
        actor_user_id=str(current_user.id),
        severity=Severity.INFO,
        after_json='{"status": "approved"}',
    )

    await db.commit()
    return {"status": "approved", "professional_status": "active"}


@router.post("/{request_id}/reject")
async def reject_verification(
    request_id: str,
    payload: ReasonPayload,
    current_user: User = Depends(require_role([RoleCode.ADMIN_VALIDATION, RoleCode.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    reason = payload.reason

    verification = await _get_verification_or_404(db, request_id)

    if not reason or not reason.strip():
        raise HTTPException(status_code=400, detail="Reason is required for rejection")

    verification.status = VerificationRequestStatus.REJECTED
    verification.decision_at = datetime.utcnow()
    verification.decision_reason = reason
    verification.reviewed_by = str(current_user.id)

    professional_result = await db.execute(select(Professional).where(Professional.id == verification.professional_id))
    professional = professional_result.scalar_one_or_none()

    if professional:
        professional.onboarding_status = OnboardingStatus.REJECTED
        professional.status = ProfessionalStatus.REJECTED
        professional.is_public_profile_enabled = False
        professional.updated_at = datetime.utcnow()
        professional.updated_by = str(current_user.id)

    await _create_verification_event(
        db,
        verification_request_id=request_id,
        event_type=VerificationEventType.REJECTED,
        payload={"reason": reason},
        created_by=str(current_user.id),
    )

    await _log_audit(
        db,
        action="admin_reject_verification",
        entity_type="verification_request",
        entity_id=request_id,
        actor_user_id=str(current_user.id),
        severity=Severity.WARNING,
        after_json='{"status": "rejected", "reason": "' + reason + '"}',
    )

    await db.commit()
    return {"status": "rejected", "reason": reason}
