from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.models.role import RoleCode
from app.models.professional import Professional
from app.models.verification import VerificationRequest, VerificationRequestStatus, VerificationEvent, VerificationEventType
from app.models.audit import AuditEvent, Severity

router = APIRouter()

async def audit_log(db: AsyncSession, action: str, entity_type: str, entity_id: str, actor_user_id: str, severity: Severity = Severity.INFO, before_json: Optional[str] = None, after_json: Optional[str] = None):
    event = AuditEvent(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_user_id=actor_user_id,
        severity=severity,
        before_json=before_json,
        after_json=after_json
    )
    db.add(event)
    await db.commit()

@router.get("/verification-requests")
async def list_verification_requests(
    current_user: User = Depends(require_role([RoleCode.ADMIN_VALIDATION, RoleCode.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(VerificationRequest).where(VerificationRequest.deleted_at.is_(None)))
    return result.scalars().all()

@router.get("/verification-requests/{request_id}")
async def get_verification_request(request_id: str, current_user: User = Depends(require_role([RoleCode.ADMIN_VALIDATION, RoleCode.SUPER_ADMIN])), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VerificationRequest).where(VerificationRequest.id == request_id))
    verification = result.scalar_one_or_none()
    if not verification:
        raise HTTPException(status_code=404, detail="Verification request not found")
    return verification

@router.post("/verification-requests/{request_id}/assign")
async def assign_verification(request_id: str, current_user: User = Depends(require_role([RoleCode.ADMIN_VALIDATION, RoleCode.SUPER_ADMIN])), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VerificationRequest).where(VerificationRequest.id == request_id))
    verification = result.scalar_one_or_none()
    if not verification:
        raise HTTPException(status_code=404, detail="Verification request not found")
    
    verification.assigned_admin_id = current_user.id
    verification.status = VerificationRequestStatus.UNDER_REVIEW
    
    event = VerificationEvent(verification_request_id=request_id, event_type=VerificationEventType.ASSIGNED, created_by=current_user.id)
    db.add(event)
    await audit_log(db, "assign_verification", "verification_request", request_id, current_user.id)
    await db.commit()
    
    return {"status": "assigned"}

@router.post("/verification-requests/{request_id}/request-correction")
async def request_correction(request_id: str, reason: str, current_user: User = Depends(require_role([RoleCode.ADMIN_VALIDATION, RoleCode.SUPER_ADMIN])), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VerificationRequest).where(VerificationRequest.id == request_id))
    verification = result.scalar_one_or_none()
    if not verification:
        raise HTTPException(status_code=404, detail="Verification request not found")
    
    verification.status = VerificationRequestStatus.NEEDS_CORRECTION
    
    professional_result = await db.execute(select(Professional).where(Professional.id == verification.professional_id))
    professional = professional_result.scalar_one_or_none()
    if professional:
        professional.onboarding_status = "needs_correction"
    
    event = VerificationEvent(
        verification_request_id=request_id,
        event_type=VerificationEventType.CORRECTION_REQUESTED,
        event_payload_json=f'{{"reason": "{reason}"}}',
        created_by=current_user.id
    )
    db.add(event)
    await audit_log(db, "request_correction", "verification_request", request_id, current_user.id, Severity.WARNING, after_json=f'{{"reason": "{reason}"}}')
    await db.commit()
    
    return {"status": "correction_requested"}

@router.post("/verification-requests/{request_id}/approve")
async def approve_verification(request_id: str, current_user: User = Depends(require_role([RoleCode.ADMIN_VALIDATION, RoleCode.SUPER_ADMIN])), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VerificationRequest).where(VerificationRequest.id == request_id))
    verification = result.scalar_one_or_none()
    if not verification:
        raise HTTPException(status_code=404, detail="Verification request not found")
    
    verification.status = VerificationRequestStatus.APPROVED
    verification.decision_at = __import__("datetime").datetime.utcnow()
    verification.reviewed_by = current_user.id
    
    professional_result = await db.execute(select(Professional).where(Professional.id == verification.professional_id))
    professional = professional_result.scalar_one_or_none()
    if professional:
        professional.onboarding_status = "approved"
        professional.status = "active"
        professional.is_public_profile_enabled = True
    
    event = VerificationEvent(verification_request_id=request_id, event_type=VerificationEventType.APPROVED, created_by=current_user.id)
    db.add(event)
    await audit_log(db, "approve_verification", "verification_request", request_id, current_user.id, Severity.INFO, after_json='{"status": "approved"}')
    await db.commit()
    
    return {"status": "approved"}

@router.post("/verification-requests/{request_id}/reject")
async def reject_verification(request_id: str, reason: str, current_user: User = Depends(require_role([RoleCode.ADMIN_VALIDATION, RoleCode.SUPER_ADMIN])), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VerificationRequest).where(VerificationRequest.id == request_id))
    verification = result.scalar_one_or_none()
    if not verification:
        raise HTTPException(status_code=404, detail="Verification request not found")
    
    verification.status = VerificationRequestStatus.REJECTED
    verification.decision_at = __import__("datetime").datetime.utcnow()
    verification.decision_reason = reason
    verification.reviewed_by = current_user.id
    
    professional_result = await db.execute(select(Professional).where(Professional.id == verification.professional_id))
    professional = professional_result.scalar_one_or_none()
    if professional:
        professional.onboarding_status = "rejected"
        professional.status = "rejected"
    
    event = VerificationEvent(
        verification_request_id=request_id,
        event_type=VerificationEventType.REJECTED,
        event_payload_json=f'{{"reason": "{reason}"}}',
        created_by=current_user.id
    )
    db.add(event)
    await audit_log(db, "reject_verification", "verification_request", request_id, current_user.id, Severity.WARNING, after_json=f'{{"reason": "{reason}"}}')
    await db.commit()
    
    return {"status": "rejected"}

@router.get("/professionals/{professional_id}")
async def get_professional_detail(professional_id: str, current_user: User = Depends(require_role([RoleCode.ADMIN_VALIDATION, RoleCode.SUPER_ADMIN])), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Professional).where(Professional.id == professional_id))
    professional = result.scalar_one_or_none()
    if not professional:
        raise HTTPException(status_code=404, detail="Professional not found")
    return professional

@router.get("/audit-events")
async def list_audit_events(
    current_user: User = Depends(require_role([RoleCode.ADMIN_VALIDATION, RoleCode.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(AuditEvent).order_by(AuditEvent.occurred_at.desc()).limit(100))
    return result.scalars().all()