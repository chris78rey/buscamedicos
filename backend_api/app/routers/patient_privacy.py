from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.step7_services import PatientConsentService, ClinicalAccessLoggingService, PrivacyPolicyService
from app.schemas.step7_schemas import (
    ConsentCreate, ConsentResponse,
    PrivacyPolicyVersionResponse,
    ClinicalAccessLogResponse,
)

router = APIRouter(prefix="/privacy", tags=["patient-privacy"])



@router.get("/consents", response_model=List[ConsentResponse])
async def list_consents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = PatientConsentService(db)
    consents = await service.get_active_consents(str(current_user.id))
    return [
        ConsentResponse(
            id=c.id,
            patient_id=c.patient_id,
            consent_type=c.consent_type,
            status=c.status,
            granted_at=c.granted_at,
            revoked_at=c.revoked_at,
            expires_at=c.expires_at,
            source=c.source,
            evidence_file_id=c.evidence_file_id,
            granted_by_user_id=c.granted_by_user_id,
            notes=c.notes,
        )
        for c in consents
    ]


@router.post("/consents", response_model=ConsentResponse)
async def grant_consent(
    data: ConsentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = PatientConsentService(db)
    consent = await service.grant_consent(
        patient_id=str(current_user.id),
        consent_type=data.consent_type,
        source=data.source,
        granted_by_user_id=str(current_user.id),
        evidence_file_id=data.evidence_file_id,
        expires_at=data.expires_at,
        notes=data.notes,
    )
    return ConsentResponse(
        id=consent.id,
        patient_id=consent.patient_id,
        consent_type=consent.consent_type,
        status=consent.status,
        granted_at=consent.granted_at,
        revoked_at=consent.revoked_at,
        expires_at=consent.expires_at,
        source=consent.source,
        evidence_file_id=consent.evidence_file_id,
        granted_by_user_id=consent.granted_by_user_id,
        notes=consent.notes,
    )


@router.post("/consents/{consent_id}/revoke", response_model=ConsentResponse)
async def revoke_consent(
    consent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = PatientConsentService(db)
    consent = await service.revoke_consent(consent_id, str(current_user.id))
    return ConsentResponse(
        id=consent.id,
        patient_id=consent.patient_id,
        consent_type=consent.consent_type,
        status=consent.status,
        granted_at=consent.granted_at,
        revoked_at=consent.revoked_at,
        expires_at=consent.expires_at,
        source=consent.source,
        evidence_file_id=consent.evidence_file_id,
        granted_by_user_id=consent.granted_by_user_id,
        notes=consent.notes,
    )


@router.get("/policies/active", response_model=List[PrivacyPolicyVersionResponse])
async def get_active_policies(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = PrivacyPolicyService(db)
    policies = await service.get_active_policies()
    return [
        PrivacyPolicyVersionResponse(
            id=p.id,
            policy_type=p.policy_type,
            version_code=p.version_code,
            content_markdown=p.content_markdown,
            is_active=p.is_active,
            published_at=p.published_at,
            created_at=p.created_at,
        )
        for p in policies
    ]


@router.get("/access-log/me", response_model=List[ClinicalAccessLogResponse])
async def get_my_access_log(
    from_date=None,
    to_date=None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ClinicalAccessLoggingService(db)
    logs = await service.get_logs(
        actor_user_id=str(current_user.id),
        limit=100
    )
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
            created_at=log.created_at,
        )
        for log in logs
    ]
