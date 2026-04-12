from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.privacy_authorization import require_admin_privacy
from app.models.user import User
from app.services.step7_services import (
    PrivacyPolicyService, ResourceClassificationService,
    ExceptionalAccessRequestService, ClinicalAccessLoggingService,
    RetentionPolicyService, PrivacyIncidentService,
    ProcessingActivityService,
)
from app.schemas.step7_schemas import (
    PrivacyPolicyVersionCreate, PrivacyPolicyVersionResponse,
    ResourceAccessPolicyUpdate, ResourceAccessPolicyResponse,
    ExceptionalAccessRequestResponse, ApproveAccessRequest, ApproveAccessResponse,
    RejectAccessRequest, RevokeAccessRequest,
    ClinicalAccessLogExportResponse,
    ProcessingActivityCreate, ProcessingActivityResponse,
    RetentionPolicyCreate, RetentionPolicyResponse,
    PrivacyIncidentCreate, PrivacyIncidentResponse, PrivacyIncidentAssign,
    PrivacyIncidentResolve, PrivacyIncidentContain, PrivacyIncidentDismiss,
)

router = APIRouter(prefix="/privacy", tags=["admin-privacy"])



def _req_response(req) -> ExceptionalAccessRequestResponse:
    return ExceptionalAccessRequestResponse(
        id=req.id, requester_user_id=req.requester_user_id,
        requester_role_code=req.requester_role_code, patient_id=req.patient_id,
        target_user_id=req.target_user_id, resource_type=req.resource_type,
        resource_id=req.resource_id, scope_type=req.scope_type,
        justification=req.justification, business_basis=req.business_basis,
        requested_minutes=req.requested_minutes, status=req.status,
        requires_patient_authorization=req.requires_patient_authorization,
        patient_consent_id=req.patient_consent_id,
        approved_by_user_id=req.approved_by_user_id, approved_at=req.approved_at,
        rejected_by_user_id=req.rejected_by_user_id, rejected_at=req.rejected_at,
        rejection_reason=req.rejection_reason, starts_at=req.starts_at,
        expires_at=req.expires_at, revoked_by_user_id=req.revoked_by_user_id,
        revoked_at=req.revoked_at, revoke_reason=req.revoke_reason,
        created_at=req.created_at,
    )


# PRIVACY POLICIES
@router.get("/policies", response_model=List[PrivacyPolicyVersionResponse])
async def list_policies(
    policy_type: Optional[str] = Query(None),
    _: User = Depends(require_admin_privacy),
    db: AsyncSession = Depends(get_db)
):
    service = PrivacyPolicyService(db)
    policies = await service.list_policies(policy_type)
    return [
        PrivacyPolicyVersionResponse(
            id=p.id, policy_type=p.policy_type, version_code=p.version_code,
            content_markdown=p.content_markdown, is_active=p.is_active,
            published_at=p.published_at, created_at=p.created_at,
        )
        for p in policies
    ]


@router.post("/policies", response_model=PrivacyPolicyVersionResponse)
async def create_policy(
    data: PrivacyPolicyVersionCreate,
    _: User = Depends(require_admin_privacy),
    db: AsyncSession = Depends(get_db)
):
    service = PrivacyPolicyService(db)
    policy = await service.create_policy(
        policy_type=data.policy_type, version_code=data.version_code,
        content_markdown=data.content_markdown,
    )
    return PrivacyPolicyVersionResponse(
        id=policy.id, policy_type=policy.policy_type,
        version_code=policy.version_code, content_markdown=policy.content_markdown,
        is_active=policy.is_active, published_at=policy.published_at,
        created_at=policy.created_at,
    )


@router.post("/policies/{policy_id}/publish", response_model=PrivacyPolicyVersionResponse)
async def publish_policy(
    policy_id: str,
    _: User = Depends(require_admin_privacy),
    db: AsyncSession = Depends(get_db)
):
    service = PrivacyPolicyService(db)
    policy = await service.publish_policy(policy_id)
    return PrivacyPolicyVersionResponse(
        id=policy.id, policy_type=policy.policy_type,
        version_code=policy.version_code, content_markdown=policy.content_markdown,
        is_active=policy.is_active, published_at=policy.published_at,
        created_at=policy.created_at,
    )


# RESOURCE ACCESS POLICIES
@router.get("/resource-policies", response_model=List[ResourceAccessPolicyResponse])
async def list_resource_policies(
    _: User = Depends(require_admin_privacy),
    db: AsyncSession = Depends(get_db)
):
    service = ResourceClassificationService(db)
    policies = await service.get_all_policies()
    return [
        ResourceAccessPolicyResponse(
            resource_type=p.resource_type, classification_code=p.classification_code,
            access_mode=p.access_mode, requires_relationship=p.requires_relationship,
            requires_patient_authorization=p.requires_patient_authorization,
            requires_justification=p.requires_justification,
            max_access_minutes=p.max_access_minutes, allow_download=p.allow_download,
            is_active=p.is_active,
        )
        for p in policies
    ]


@router.put("/resource-policies/{resource_type}", response_model=ResourceAccessPolicyResponse)
async def update_resource_policy(
    resource_type: str,
    data: ResourceAccessPolicyUpdate,
    _: User = Depends(require_admin_privacy),
    db: AsyncSession = Depends(get_db)
):
    service = ResourceClassificationService(db)
    policy = await service.upsert_policy(
        resource_type=resource_type,
        classification_code=data.classification_code,
        access_mode=data.access_mode,
        requires_relationship=data.requires_relationship,
        requires_patient_authorization=data.requires_patient_authorization,
        requires_justification=data.requires_justification,
        max_access_minutes=data.max_access_minutes,
        allow_download=data.allow_download,
    )
    return ResourceAccessPolicyResponse(
        resource_type=policy.resource_type, classification_code=policy.classification_code,
        access_mode=policy.access_mode, requires_relationship=policy.requires_relationship,
        requires_patient_authorization=policy.requires_patient_authorization,
        requires_justification=policy.requires_justification,
        max_access_minutes=policy.max_access_minutes, allow_download=policy.allow_download,
        is_active=policy.is_active,
    )


# EXCEPTIONAL ACCESS REQUESTS
@router.get("/exceptional-access-requests", response_model=List[ExceptionalAccessRequestResponse])
async def list_access_requests(
    status_filter: Optional[str] = Query(None),
    _: User = Depends(require_admin_privacy),
    db: AsyncSession = Depends(get_db)
):
    service = ExceptionalAccessRequestService(db)
    requests = await service.list_requests(status_filter=status_filter)
    return [_req_response(r) for r in requests]


@router.get("/exceptional-access-requests/{request_id}", response_model=ExceptionalAccessRequestResponse)
async def get_access_request(
    request_id: str,
    _: User = Depends(require_admin_privacy),
    db: AsyncSession = Depends(get_db)
):
    service = ExceptionalAccessRequestService(db)
    req = await service.get_request(request_id)
    if not req:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Request not found")
    return _req_response(req)


@router.post("/exceptional-access-requests/{request_id}/approve", response_model=ApproveAccessResponse)
async def approve_access_request(
    request_id: str,
    data: ApproveAccessRequest,
    current_user: User = Depends(require_admin_privacy),
    db: AsyncSession = Depends(get_db)
):
    service = ExceptionalAccessRequestService(db)
    req, grant = await service.approve_request(
        request_id=request_id,
        approver_user_id=str(current_user.id),
        expires_at=data.expires_at,
        starts_at=data.starts_at,
        approval_note=data.approval_note,
    )
    return ApproveAccessResponse(
        request_id=req.id, status=req.status,
        grant_id=grant.id, granted_until=grant.expires_at,
    )


@router.post("/exceptional-access-requests/{request_id}/reject")
async def reject_access_request(
    request_id: str,
    data: RejectAccessRequest,
    current_user: User = Depends(require_admin_privacy),
    db: AsyncSession = Depends(get_db)
):
    service = ExceptionalAccessRequestService(db)
    req = await service.reject_request(
        request_id=request_id,
        rejecter_user_id=str(current_user.id),
        rejection_reason=data.reason,
    )
    return _req_response(req)


@router.post("/exceptional-access-requests/{request_id}/revoke")
async def revoke_access_request(
    request_id: str,
    data: RevokeAccessRequest,
    current_user: User = Depends(require_admin_privacy),
    db: AsyncSession = Depends(get_db)
):
    service = ExceptionalAccessRequestService(db)
    req = await service.get_request(request_id)
    if not req:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Request not found")
    from app.models.step7_models import ExceptionalAccessGrant
    from sqlalchemy import select
    grant_result = await db.execute(
        select(ExceptionalAccessGrant).where(
            ExceptionalAccessGrant.request_id == request_id,
            ExceptionalAccessGrant.deleted_at == None
        )
    )
    grant = grant_result.scalar_one_or_none()
    if not grant:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Grant not found")
    grant = await service.revoke_grant(
        grant_id=grant.id,
        revoker_user_id=str(current_user.id),
        reason=data.reason,
    )
    return {"status": grant.status, "grant_id": grant.id}


# ACCESS LOGS
@router.get("/access-logs", response_model=List[ClinicalAccessLogExportResponse])
async def list_access_logs(
    actor_user_id: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    _: User = Depends(require_admin_privacy),
    db: AsyncSession = Depends(get_db)
):
    service = ClinicalAccessLoggingService(db)
    logs = await service.get_logs(
        actor_user_id=actor_user_id,
        resource_type=resource_type,
        from_date=from_date,
        to_date=to_date,
        limit=200,
    )
    return [
        ClinicalAccessLogExportResponse(
            id=log.id, actor_user_id=log.actor_user_id,
            actor_role_code=log.actor_role_code, patient_id=log.patient_id,
            target_user_id=log.target_user_id, resource_type=log.resource_type,
            resource_id=log.resource_id, access_mode=log.access_mode,
            action=log.action, decision=log.decision,
            exceptional_access_request_id=log.exceptional_access_request_id,
            created_at=log.created_at,
        )
        for log in logs
    ]


@router.get("/access-logs/export-meta", response_model=List[ClinicalAccessLogExportResponse])
async def export_access_logs_meta(
    actor_user_id: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    _: User = Depends(require_admin_privacy),
    db: AsyncSession = Depends(get_db)
):
    service = ClinicalAccessLoggingService(db)
    return await service.export_meta(
        actor_user_id=actor_user_id,
        resource_type=resource_type,
        from_date=from_date,
        to_date=to_date,
    )


# PROCESSING ACTIVITIES
@router.get("/processing-activities", response_model=List[ProcessingActivityResponse])
async def list_processing_activities(
    _: User = Depends(require_admin_privacy),
    db: AsyncSession = Depends(get_db)
):
    service = ProcessingActivityService(db)
    activities = await service.list_activities()
    return [
        ProcessingActivityResponse(
            id=a.id, code=a.code, module_name=a.module_name,
            purpose=a.purpose, data_categories_json=a.data_categories_json,
            subject_categories_json=a.subject_categories_json,
            legal_basis=a.legal_basis, retention_policy_id=a.retention_policy_id,
            is_sensitive=a.is_sensitive, is_active=a.is_active,
        )
        for a in activities
    ]


@router.post("/processing-activities", response_model=ProcessingActivityResponse)
async def create_processing_activity(
    data: ProcessingActivityCreate,
    _: User = Depends(require_admin_privacy),
    db: AsyncSession = Depends(get_db)
):
    service = ProcessingActivityService(db)
    activity = await service.create(
        code=data.code, module_name=data.module_name, purpose=data.purpose,
        data_categories=data.data_categories,
        subject_categories=data.subject_categories,
        legal_basis=data.legal_basis,
        retention_policy_id=data.retention_policy_id,
        is_sensitive=data.is_sensitive,
    )
    return ProcessingActivityResponse(
        id=activity.id, code=activity.code, module_name=activity.module_name,
        purpose=activity.purpose, data_categories_json=activity.data_categories_json,
        subject_categories_json=activity.subject_categories_json,
        legal_basis=activity.legal_basis, retention_policy_id=activity.retention_policy_id,
        is_sensitive=activity.is_sensitive, is_active=activity.is_active,
    )


@router.put("/processing-activities/{activity_id}", response_model=ProcessingActivityResponse)
async def update_processing_activity(
    activity_id: str,
    data: ProcessingActivityCreate,
    _: User = Depends(require_admin_privacy),
    db: AsyncSession = Depends(get_db)
):
    service = ProcessingActivityService(db)
    activity = await service.update(
        activity_id=activity_id,
        purpose=data.purpose,
        legal_basis=data.legal_basis,
        is_sensitive=data.is_sensitive,
    )
    return ProcessingActivityResponse(
        id=activity.id, code=activity.code, module_name=activity.module_name,
        purpose=activity.purpose, data_categories_json=activity.data_categories_json,
        subject_categories_json=activity.subject_categories_json,
        legal_basis=activity.legal_basis, retention_policy_id=activity.retention_policy_id,
        is_sensitive=activity.is_sensitive, is_active=activity.is_active,
    )


# RETENTION POLICIES
@router.get("/retention-policies", response_model=List[RetentionPolicyResponse])
async def list_retention_policies(
    _: User = Depends(require_admin_privacy),
    db: AsyncSession = Depends(get_db)
):
    service = RetentionPolicyService(db)
    policies = await service.list_policies()
    return [
        RetentionPolicyResponse(
            id=p.id, code=p.code, resource_type=p.resource_type,
            retention_days=p.retention_days, archive_after_days=p.archive_after_days,
            delete_mode=p.delete_mode, description=p.description, is_active=p.is_active,
        )
        for p in policies
    ]


@router.post("/retention-policies", response_model=RetentionPolicyResponse)
async def create_retention_policy(
    data: RetentionPolicyCreate,
    _: User = Depends(require_admin_privacy),
    db: AsyncSession = Depends(get_db)
):
    service = RetentionPolicyService(db)
    policy = await service.create_policy(
        code=data.code, resource_type=data.resource_type,
        delete_mode=data.delete_mode,
        retention_days=data.retention_days,
        archive_after_days=data.archive_after_days,
        description=data.description,
    )
    return RetentionPolicyResponse(
        id=policy.id, code=policy.code, resource_type=policy.resource_type,
        retention_days=policy.retention_days, archive_after_days=policy.archive_after_days,
        delete_mode=policy.delete_mode, description=policy.description, is_active=policy.is_active,
    )


@router.put("/retention-policies/{policy_id}", response_model=RetentionPolicyResponse)
async def update_retention_policy(
    policy_id: str,
    data: RetentionPolicyCreate,
    _: User = Depends(require_admin_privacy),
    db: AsyncSession = Depends(get_db)
):
    service = RetentionPolicyService(db)
    policy = await service.update_policy(
        policy_id=policy_id,
        retention_days=data.retention_days,
        archive_after_days=data.archive_after_days,
        description=data.description,
    )
    return RetentionPolicyResponse(
        id=policy.id, code=policy.code, resource_type=policy.resource_type,
        retention_days=policy.retention_days, archive_after_days=policy.archive_after_days,
        delete_mode=policy.delete_mode, description=policy.description, is_active=policy.is_active,
    )


# PRIVACY INCIDENTS
@router.get("/incidents", response_model=List[PrivacyIncidentResponse])
async def list_incidents(
    status_filter: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    _: User = Depends(require_admin_privacy),
    db: AsyncSession = Depends(get_db)
):
    service = PrivacyIncidentService(db)
    incidents = await service.list_incidents(
        status_filter=status_filter, severity=severity,
    )
    return [
        PrivacyIncidentResponse(
            id=i.id, incident_code=i.incident_code, detected_at=i.detected_at,
            reported_by_user_id=i.reported_by_user_id, severity=i.severity,
            incident_type=i.incident_type, description=i.description,
            affected_resource_type=i.affected_resource_type,
            affected_resource_id=i.affected_resource_id, status=i.status,
            assigned_admin_id=i.assigned_admin_id,
            resolution_summary=i.resolution_summary, resolved_at=i.resolved_at,
        )
        for i in incidents
    ]


@router.get("/incidents/{incident_id}", response_model=PrivacyIncidentResponse)
async def get_incident(
    incident_id: str,
    _: User = Depends(require_admin_privacy),
    db: AsyncSession = Depends(get_db)
):
    service = PrivacyIncidentService(db)
    incident = await service.get_incident(incident_id)
    if not incident:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Incident not found")
    return PrivacyIncidentResponse(
        id=incident.id, incident_code=incident.incident_code,
        detected_at=incident.detected_at, reported_by_user_id=incident.reported_by_user_id,
        severity=incident.severity, incident_type=incident.incident_type,
        description=incident.description,
        affected_resource_type=incident.affected_resource_type,
        affected_resource_id=incident.affected_resource_id, status=incident.status,
        assigned_admin_id=incident.assigned_admin_id,
        resolution_summary=incident.resolution_summary, resolved_at=incident.resolved_at,
    )


@router.post("/incidents", response_model=PrivacyIncidentResponse)
async def create_incident(
    data: PrivacyIncidentCreate,
    current_user: User = Depends(require_admin_privacy),
    db: AsyncSession = Depends(get_db)
):
    service = PrivacyIncidentService(db)
    incident = await service.create_incident(
        incident_type=data.incident_type,
        description=data.description,
        severity=data.severity,
        detected_at=datetime.utcnow(),
        affected_resource_type=data.affected_resource_type,
        affected_resource_id=data.affected_resource_id,
    )
    return PrivacyIncidentResponse(
        id=incident.id, incident_code=incident.incident_code,
        detected_at=incident.detected_at, reported_by_user_id=incident.reported_by_user_id,
        severity=incident.severity, incident_type=incident.incident_type,
        description=incident.description,
        affected_resource_type=incident.affected_resource_type,
        affected_resource_id=incident.affected_resource_id, status=incident.status,
        assigned_admin_id=incident.assigned_admin_id,
        resolution_summary=incident.resolution_summary, resolved_at=incident.resolved_at,
    )


@router.post("/incidents/{incident_id}/assign", response_model=PrivacyIncidentResponse)
async def assign_incident(
    incident_id: str,
    data: PrivacyIncidentAssign,
    current_user: User = Depends(require_admin_privacy),
    db: AsyncSession = Depends(get_db)
):
    service = PrivacyIncidentService(db)
    incident = await service.assign_incident(incident_id, data.admin_id)
    return PrivacyIncidentResponse(
        id=incident.id, incident_code=incident.incident_code,
        detected_at=incident.detected_at, reported_by_user_id=incident.reported_by_user_id,
        severity=incident.severity, incident_type=incident.incident_type,
        description=incident.description,
        affected_resource_type=incident.affected_resource_type,
        affected_resource_id=incident.affected_resource_id, status=incident.status,
        assigned_admin_id=incident.assigned_admin_id,
        resolution_summary=incident.resolution_summary, resolved_at=incident.resolved_at,
    )


@router.post("/incidents/{incident_id}/contain", response_model=PrivacyIncidentResponse)
async def contain_incident(
    incident_id: str,
    current_user: User = Depends(require_admin_privacy),
    db: AsyncSession = Depends(get_db)
):
    service = PrivacyIncidentService(db)
    incident = await service.contain_incident(incident_id, str(current_user.id))
    return PrivacyIncidentResponse(
        id=incident.id, incident_code=incident.incident_code,
        detected_at=incident.detected_at, reported_by_user_id=incident.reported_by_user_id,
        severity=incident.severity, incident_type=incident.incident_type,
        description=incident.description,
        affected_resource_type=incident.affected_resource_type,
        affected_resource_id=incident.affected_resource_id, status=incident.status,
        assigned_admin_id=incident.assigned_admin_id,
        resolution_summary=incident.resolution_summary, resolved_at=incident.resolved_at,
    )


@router.post("/incidents/{incident_id}/resolve", response_model=PrivacyIncidentResponse)
async def resolve_incident(
    incident_id: str,
    data: PrivacyIncidentResolve,
    current_user: User = Depends(require_admin_privacy),
    db: AsyncSession = Depends(get_db)
):
    service = PrivacyIncidentService(db)
    incident = await service.resolve_incident(
        incident_id, str(current_user.id), data.summary,
    )
    return PrivacyIncidentResponse(
        id=incident.id, incident_code=incident.incident_code,
        detected_at=incident.detected_at, reported_by_user_id=incident.reported_by_user_id,
        severity=incident.severity, incident_type=incident.incident_type,
        description=incident.description,
        affected_resource_type=incident.affected_resource_type,
        affected_resource_id=incident.affected_resource_id, status=incident.status,
        assigned_admin_id=incident.assigned_admin_id,
        resolution_summary=incident.resolution_summary, resolved_at=incident.resolved_at,
    )


@router.post("/incidents/{incident_id}/dismiss", response_model=PrivacyIncidentResponse)
async def dismiss_incident(
    incident_id: str,
    data: PrivacyIncidentDismiss,
    current_user: User = Depends(require_admin_privacy),
    db: AsyncSession = Depends(get_db)
):
    service = PrivacyIncidentService(db)
    incident = await service.dismiss_incident(incident_id, str(current_user.id))
    return PrivacyIncidentResponse(
        id=incident.id, incident_code=incident.incident_code,
        detected_at=incident.detected_at, reported_by_user_id=incident.reported_by_user_id,
        severity=incident.severity, incident_type=incident.incident_type,
        description=incident.description,
        affected_resource_type=incident.affected_resource_type,
        affected_resource_id=incident.affected_resource_id, status=incident.status,
        assigned_admin_id=incident.assigned_admin_id,
        resolution_summary=incident.resolution_summary, resolved_at=incident.resolved_at,
    )
