from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.step7_services import (
    ExceptionalAccessRequestService, ClinicalAccessLoggingService
)
from app.schemas.step7_schemas import (
    ExceptionalAccessRequestCreate, ExceptionalAccessRequestResponse,
    ClinicalAccessLogResponse,
)

router = APIRouter(prefix="/me/privacy", tags=["professional-privacy"])



@router.post("/exceptional-access-requests", response_model=ExceptionalAccessRequestResponse)
async def create_exceptional_access_request(
    data: ExceptionalAccessRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ExceptionalAccessRequestService(db)
    req = await service.create_request(
        requester_user_id=str(current_user.id),
        requester_role_code=current_user.role_code,
        resource_type=data.resource_type,
        scope_type=data.scope_type,
        justification=data.justification,
        requested_minutes=data.requested_minutes,
        patient_id=data.patient_id,
        target_user_id=data.target_user_id,
        resource_id=data.resource_id,
        business_basis=data.business_basis,
    )
    return ExceptionalAccessRequestResponse(
        id=req.id,
        requester_user_id=req.requester_user_id,
        requester_role_code=req.requester_role_code,
        patient_id=req.patient_id,
        target_user_id=req.target_user_id,
        resource_type=req.resource_type,
        resource_id=req.resource_id,
        scope_type=req.scope_type,
        justification=req.justification,
        business_basis=req.business_basis,
        requested_minutes=req.requested_minutes,
        status=req.status,
        requires_patient_authorization=req.requires_patient_authorization,
        patient_consent_id=req.patient_consent_id,
        approved_by_user_id=req.approved_by_user_id,
        approved_at=req.approved_at,
        rejected_by_user_id=req.rejected_by_user_id,
        rejected_at=req.rejected_at,
        rejection_reason=req.rejection_reason,
        starts_at=req.starts_at,
        expires_at=req.expires_at,
        revoked_by_user_id=req.revoked_by_user_id,
        revoked_at=req.revoked_at,
        revoke_reason=req.revoke_reason,
        created_at=req.created_at,
    )


@router.get("/exceptional-access-requests", response_model=List[ExceptionalAccessRequestResponse])
async def list_my_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ExceptionalAccessRequestService(db)
    requests = await service.list_requests(requester_user_id=str(current_user.id))
    return [
        ExceptionalAccessRequestResponse(
            id=r.id,
            requester_user_id=r.requester_user_id,
            requester_role_code=r.requester_role_code,
            patient_id=r.patient_id,
            target_user_id=r.target_user_id,
            resource_type=r.resource_type,
            resource_id=r.resource_id,
            scope_type=r.scope_type,
            justification=r.justification,
            business_basis=r.business_basis,
            requested_minutes=r.requested_minutes,
            status=r.status,
            requires_patient_authorization=r.requires_patient_authorization,
            patient_consent_id=r.patient_consent_id,
            approved_by_user_id=r.approved_by_user_id,
            approved_at=r.approved_at,
            rejected_by_user_id=r.rejected_by_user_id,
            rejected_at=r.rejected_at,
            rejection_reason=r.rejection_reason,
            starts_at=r.starts_at,
            expires_at=r.expires_at,
            revoked_by_user_id=r.revoked_by_user_id,
            revoked_at=r.revoked_at,
            revoke_reason=r.revoke_reason,
            created_at=r.created_at,
        )
        for r in requests
    ]


@router.get("/access-log/me", response_model=List[ClinicalAccessLogResponse])
async def get_my_access_log(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ClinicalAccessLoggingService(db)
    logs = await service.get_logs(actor_user_id=str(current_user.id), limit=100)
    return [
        ClinicalAccessLogResponse(
            id=log.id,
            actor_user_id=log.actor_user_id,
            actor_role_code=log.actor_role_code,
            patient_id=log.patient_id,
            target_user_id=log.target_user_id,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            access_mode=log.access_mode,
            action=log.action,
            decision=log.decision,
            exceptional_access_request_id=log.exceptional_access_request_id,
            justification=log.justification,
            created_at=log.created_at,
        )
        for log in logs
    ]
