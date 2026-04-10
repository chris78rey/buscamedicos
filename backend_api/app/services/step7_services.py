import uuid
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, text
from fastapi import HTTPException, status

from app.models.step7_models import (
    DataClassification, ClassificationCode,
    ResourceAccessPolicy, AccessMode,
    PatientPrivacyConsent, ConsentType, ConsentStatus, ConsentSource,
    ExceptionalAccessRequest, ExceptionalAccessRequestStatus, ScopeType,
    ExceptionalAccessGrant, GrantStatus,
    ClinicalAccessLog, ClinicalAccessMode, ClinicalAccessAction, ClinicalAccessDecision,
    ProcessingActivity,
    RetentionPolicy, DeleteMode,
    PrivacyIncident, PrivacyIncidentEvent, IncidentSeverity, IncidentType, IncidentStatus, IncidentEventType,
    PrivacyPolicyVersion, PrivacyPolicyType, PrivacyPolicyAcceptance, AcceptanceStatus,
    RESOURCE_TYPES,
)
from app.models.step2_models import Appointment, AppointmentStatus
from app.models.user import User
from app.models.audit import AuditEvent, Severity


# =============================================================================
# 1. Resource Classification Service
# =============================================================================

class ResourceClassificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_classification(self, resource_type: str) -> Optional[ResourceAccessPolicy]:
        result = await self.db.execute(
            select(ResourceAccessPolicy).where(
                and_(
                    ResourceAccessPolicy.resource_type == resource_type,
                    ResourceAccessPolicy.is_active == True,
                    ResourceAccessPolicy.deleted_at == None
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_all_policies(self) -> List[ResourceAccessPolicy]:
        result = await self.db.execute(
            select(ResourceAccessPolicy).where(
                and_(
                    ResourceAccessPolicy.is_active == True,
                    ResourceAccessPolicy.deleted_at == None
                )
            )
        )
        return list(result.scalars().all())

    async def upsert_policy(
        self,
        resource_type: str,
        classification_code: str,
        access_mode: str,
        requires_relationship: bool = True,
        requires_patient_authorization: bool = False,
        requires_justification: bool = False,
        max_access_minutes: Optional[int] = None,
        allow_download: bool = False
    ) -> ResourceAccessPolicy:
        existing = await self.get_classification(resource_type)
        if existing:
            existing.classification_code = classification_code
            existing.access_mode = access_mode
            existing.requires_relationship = requires_relationship
            existing.requires_patient_authorization = requires_patient_authorization
            existing.requires_justification = requires_justification
            existing.max_access_minutes = max_access_minutes
            existing.allow_download = allow_download
            existing.version = str(int(existing.version) + 1)
            await self.db.flush()
            return existing
        policy = ResourceAccessPolicy(
            id=str(uuid.uuid4()),
            resource_type=resource_type,
            classification_code=classification_code,
            access_mode=access_mode,
            requires_relationship=requires_relationship,
            requires_patient_authorization=requires_patient_authorization,
            requires_justification=requires_justification,
            max_access_minutes=max_access_minutes,
            allow_download=allow_download,
            is_active=True,
        )
        self.db.add(policy)
        await self.db.flush()
        return policy


# =============================================================================
# 2. Contextual Access Decision Service
# =============================================================================

class ContextualAccessDecisionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.classification_service = ResourceClassificationService(db)

    async def _has_care_relationship(self, professional_id: str, patient_id: str) -> bool:
        result = await self.db.execute(
            select(Appointment).where(
                and_(
                    Appointment.professional_id == professional_id,
                    Appointment.patient_id == patient_id,
                    Appointment.status.in_([AppointmentStatus.COMPLETED, AppointmentStatus.CONFIRMED])
                )
            ).limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def _has_active_sanction(self, user_id: str) -> bool:
        from app.models.step6_models import AccountSanction, SanctionStatus
        result = await self.db.execute(
            select(AccountSanction).where(
                and_(
                    AccountSanction.target_id == user_id,
                    AccountSanction.target_type == "user",
                    AccountSanction.status == SanctionStatus.ACTIVE,
                    or_(
                        AccountSanction.ends_at == None,
                        AccountSanction.ends_at > datetime.utcnow()
                    )
                )
            ).limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def _has_valid_grant(
        self,
        grantee_user_id: str,
        resource_type: str,
        resource_id: Optional[str] = None
    ) -> Optional[ExceptionalAccessGrant]:
        result = await self.db.execute(
            select(ExceptionalAccessGrant).where(
                and_(
                    ExceptionalAccessGrant.grantee_user_id == grantee_user_id,
                    ExceptionalAccessGrant.resource_type == resource_type,
                    ExceptionalAccessGrant.status == GrantStatus.ACTIVE,
                    ExceptionalAccessGrant.expires_at > datetime.utcnow(),
                    or_(
                        ExceptionalAccessGrant.resource_id == resource_id,
                        ExceptionalAccessGrant.resource_id == None
                    )
                )
            ).order_by(ExceptionalAccessGrant.expires_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def _check_patient_consent(self, patient_id: str, consent_type: str) -> bool:
        result = await self.db.execute(
            select(PatientPrivacyConsent).where(
                and_(
                    PatientPrivacyConsent.patient_id == patient_id,
                    PatientPrivacyConsent.consent_type == consent_type,
                    PatientPrivacyConsent.status == ConsentStatus.GRANTED,
                    or_(
                        PatientPrivacyConsent.expires_at == None,
                        PatientPrivacyConsent.expires_at > datetime.utcnow()
                    ),
                    PatientPrivacyConsent.deleted_at == None
                )
            ).limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def evaluate_sensitive_access(
        self,
        actor_user,
        resource_type: str,
        resource_id: Optional[str] = None,
        action: str = ClinicalAccessAction.READ,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        context = context or {}
        actor_id = actor_user.id
        actor_role = getattr(actor_user, 'role_code', None)
        policy = await self.classification_service.get_classification(resource_type)

        if not policy:
            return {
                "allowed": False,
                "mode": ClinicalAccessMode.NORMAL,
                "decision_reason": f"No policy defined for resource_type={resource_type}",
                "policy_snapshot": None,
                "requires_exceptional_request": True
            }

        policy_snapshot = {
            "resource_type": resource_type,
            "classification_code": policy.classification_code,
            "access_mode": policy.access_mode,
            "requires_relationship": policy.requires_relationship,
            "requires_patient_authorization": policy.requires_patient_authorization,
            "requires_justification": policy.requires_justification,
            "allow_download": policy.allow_download,
        }

        # Admins never get normal access to clinical data
        admin_roles = {"super_admin", "admin_validation", "admin_support", "admin_moderation", "admin_privacy"}
        if actor_role in admin_roles and policy.classification_code in (
            ClassificationCode.SENSITIVE_HEALTH, ClassificationCode.RESTRICTED_LEGAL
        ):
            if policy.access_mode == AccessMode.NORMAL:
                grant = await self._has_valid_grant(actor_id, resource_type, resource_id)
                if not grant:
                    return {
                        "allowed": False,
                        "mode": ClinicalAccessMode.NORMAL,
                        "decision_reason": "Admin role requires exceptional grant for sensitive_health resources",
                        "policy_snapshot": policy_snapshot,
                        "requires_exceptional_request": True
                    }

        # privacy_auditor - read-only metadata only, never content
        if actor_role == "privacy_auditor":
            if action in (ClinicalAccessAction.READ, ClinicalAccessAction.LIST):
                if policy.classification_code in (ClassificationCode.SENSITIVE_HEALTH, ClassificationCode.RESTRICTED_LEGAL):
                    return {
                        "allowed": False,
                        "mode": ClinicalAccessMode.NORMAL,
                        "decision_reason": "privacy_auditor cannot access clinical content",
                        "policy_snapshot": policy_snapshot,
                        "requires_exceptional_request": False
                    }

        # Normal access checks
        if policy.access_mode in (AccessMode.NORMAL, AccessMode.HYBRID):
            patient_id = context.get("patient_id")

            # patient accessing own data
            if actor_role == "patient" and patient_id == actor_id:
                if not await self._has_active_sanction(actor_id):
                    return {
                        "allowed": True,
                        "mode": ClinicalAccessMode.NORMAL,
                        "decision_reason": "Patient accessing own data",
                        "policy_snapshot": policy_snapshot,
                        "requires_exceptional_request": False
                    }

            # professional with care relationship
            if actor_role == "professional" and patient_id:
                if await self._has_care_relationship(actor_id, patient_id):
                    if not await self._has_active_sanction(actor_id):
                        if policy.requires_patient_authorization:
                            if await self._check_patient_consent(patient_id, ConsentType.EXCEPTIONAL_CLINICAL_ACCESS):
                                return {
                                    "allowed": True,
                                    "mode": ClinicalAccessMode.NORMAL,
                                    "decision_reason": "Professional with care relationship and patient consent",
                                    "policy_snapshot": policy_snapshot,
                                    "requires_exceptional_request": False
                                }
                        else:
                            return {
                                "allowed": True,
                                "mode": ClinicalAccessMode.NORMAL,
                                "decision_reason": "Professional with care relationship",
                                "policy_snapshot": policy_snapshot,
                                "requires_exceptional_request": False
                            }

            # laboratory accessing exam results
            if actor_role == "laboratory":
                from app.models.step5_models import ExamOrder
                if resource_type in ("exam_result", "exam_result_file"):
                    order_result = await self.db.execute(
                        select(ExamOrder).where(ExamOrder.id == resource_id).limit(1)
                    )
                    order = order_result.scalar_one_or_none()
                    if order and order.laboratory_id == actor_id:
                        return {
                            "allowed": True,
                            "mode": ClinicalAccessMode.NORMAL,
                            "decision_reason": "Laboratory accessing assigned exam result",
                            "policy_snapshot": policy_snapshot,
                            "requires_exceptional_request": False
                        }

        # Exceptional access grant check
        if policy.access_mode in (AccessMode.EXCEPTIONAL_ONLY, AccessMode.HYBRID):
            grant = await self._has_valid_grant(actor_id, resource_type, resource_id)
            if grant:
                return {
                    "allowed": True,
                    "mode": ClinicalAccessMode.EXCEPTIONAL,
                    "decision_reason": f"Exceptional grant active, expires={grant.expires_at}",
                    "policy_snapshot": policy_snapshot,
                    "requires_exceptional_request": False,
                    "grant_id": grant.id
                }

        # Denied
        return {
            "allowed": False,
            "mode": ClinicalAccessMode.NORMAL,
            "decision_reason": "Access denied - no relationship, no grant, or policy restricts",
            "policy_snapshot": policy_snapshot,
            "requires_exceptional_request": policy.access_mode in (AccessMode.EXCEPTIONAL_ONLY, AccessMode.HYBRID)
        }


# =============================================================================
# 3. Patient Consent Service
# =============================================================================

class PatientConsentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def grant_consent(
        self,
        patient_id: str,
        consent_type: str,
        source: str,
        granted_by_user_id: Optional[str] = None,
        evidence_file_id: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        notes: Optional[str] = None
    ) -> PatientPrivacyConsent:
        # revoke existing active consent of same type
        existing = await self.db.execute(
            select(PatientPrivacyConsent).where(
                and_(
                    PatientPrivacyConsent.patient_id == patient_id,
                    PatientPrivacyConsent.consent_type == consent_type,
                    PatientPrivacyConsent.status == ConsentStatus.GRANTED,
                    PatientPrivacyConsent.deleted_at == None
                )
            )
        )
        for old in existing.scalars().all():
            old.status = ConsentStatus.REVOKED
            old.revoked_at = datetime.utcnow()

        consent = PatientPrivacyConsent(
            id=str(uuid.uuid4()),
            patient_id=patient_id,
            consent_type=consent_type,
            status=ConsentStatus.GRANTED,
            granted_at=datetime.utcnow(),
            source=source,
            evidence_file_id=evidence_file_id,
            granted_by_user_id=granted_by_user_id or patient_id,
            expires_at=expires_at,
            notes=notes,
        )
        self.db.add(consent)
        await self.db.flush()
        await self._audit_consent(patient_id, consent_type, "consent_granted", granted_by_user_id)
        return consent

    async def revoke_consent(self, consent_id: str, patient_id: str) -> PatientPrivacyConsent:
        result = await self.db.execute(
            select(PatientPrivacyConsent).where(
                and_(
                    PatientPrivacyConsent.id == consent_id,
                    PatientPrivacyConsent.patient_id == patient_id,
                    PatientPrivacyConsent.status == ConsentStatus.GRANTED,
                    PatientPrivacyConsent.deleted_at == None
                )
            )
        )
        consent = result.scalar_one_or_none()
        if not consent:
            raise HTTPException(status_code=404, detail="Active consent not found")
        consent.status = ConsentStatus.REVOKED
        consent.revoked_at = datetime.utcnow()
        consent.version = str(int(consent.version) + 1)
        await self.db.flush()
        await self._audit_consent(patient_id, consent.consent_type, "consent_revoked", patient_id)
        return consent

    async def get_active_consents(self, patient_id: str) -> List[PatientPrivacyConsent]:
        result = await self.db.execute(
            select(PatientPrivacyConsent).where(
                and_(
                    PatientPrivacyConsent.patient_id == patient_id,
                    PatientPrivacyConsent.status == ConsentStatus.GRANTED,
                    PatientPrivacyConsent.deleted_at == None,
                    or_(
                        PatientPrivacyConsent.expires_at == None,
                        PatientPrivacyConsent.expires_at > datetime.utcnow()
                    )
                )
            )
        )
        return list(result.scalars().all())

    async def get_consent(self, consent_id: str) -> Optional[PatientPrivacyConsent]:
        result = await self.db.execute(
            select(PatientPrivacyConsent).where(
                and_(
                    PatientPrivacyConsent.id == consent_id,
                    PatientPrivacyConsent.deleted_at == None
                )
            )
        )
        return result.scalar_one_or_none()

    async def _audit_consent(self, patient_id: str, consent_type: str, action: str, user_id: str):
        event = AuditEvent(
            id=str(uuid.uuid4()),
            actor_user_id=user_id,
            action=action,
            entity_type="patient_privacy_consent",
            entity_id=patient_id,
            severity=Severity.INFO,
            before_json=json.dumps({"consent_type": consent_type}),
            created_at=datetime.utcnow()
        )
        self.db.add(event)


# =============================================================================
# 4. Exceptional Access Request Service
# =============================================================================

class ExceptionalAccessRequestService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_request(
        self,
        requester_user_id: str,
        requester_role_code: str,
        resource_type: str,
        scope_type: str,
        justification: str,
        requested_minutes: int,
        patient_id: Optional[str] = None,
        target_user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        business_basis: Optional[str] = None
    ) -> ExceptionalAccessRequest:
        if not justification.strip():
            raise HTTPException(status_code=400, detail="Justification is required")
        if requested_minutes <= 0:
            raise HTTPException(status_code=400, detail="requested_minutes must be positive")

        # Check if policy requires patient authorization
        classification_service = ResourceClassificationService(self.db)
        policy = await classification_service.get_classification(resource_type)
        requires_patient_auth = policy.requires_patient_authorization if policy else False

        # If patient authorization required, we need consent
        requires_consent = False
        if requires_patient_auth and patient_id:
            consent_service = PatientConsentService(self.db)
            has_consent = await consent_service._check_patient_consent(patient_id, ConsentType.EXCEPTIONAL_CLINICAL_ACCESS)
            requires_consent = not has_consent

        status = ExceptionalAccessRequestStatus.PENDING_PATIENT_AUTHORIZATION if requires_consent else ExceptionalAccessRequestStatus.REQUESTED

        req = ExceptionalAccessRequest(
            id=str(uuid.uuid4()),
            requester_user_id=requester_user_id,
            requester_role_code=requester_role_code,
            patient_id=patient_id,
            target_user_id=target_user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            scope_type=scope_type,
            justification=justification,
            business_basis=business_basis,
            requested_minutes=requested_minutes,
            status=status,
            requires_patient_authorization=requires_consent,
        )
        self.db.add(req)
        await self.db.flush()
        await self._audit_request(req, "exceptional_access_request_created", requester_user_id)
        return req

    async def approve_request(
        self,
        request_id: str,
        approver_user_id: str,
        expires_at: datetime,
        starts_at: Optional[datetime] = None,
        approval_note: Optional[str] = None
    ) -> tuple[ExceptionalAccessRequest, ExceptionalAccessGrant]:
        if expires_at <= datetime.utcnow():
            raise HTTPException(status_code=400, detail="expires_at must be in the future")

        result = await self.db.execute(
            select(ExceptionalAccessRequest).where(
                and_(
                    ExceptionalAccessRequest.id == request_id,
                    ExceptionalAccessRequest.deleted_at == None
                )
            )
        )
        req = result.scalar_one_or_none()
        if not req:
            raise HTTPException(status_code=404, detail="Request not found")
        if req.status not in (ExceptionalAccessRequestStatus.REQUESTED, ExceptionalAccessRequestStatus.PENDING_PATIENT_AUTHORIZATION):
            raise HTTPException(status_code=409, detail=f"Cannot approve request in status={req.status}")

        # Check patient consent if required
        if req.requires_patient_authorization and req.patient_id:
            consent_service = PatientConsentService(self.db)
            has_consent = await consent_service._check_patient_consent(req.patient_id, ConsentType.EXCEPTIONAL_CLINICAL_ACCESS)
            if not has_consent:
                raise HTTPException(status_code=409, detail="Patient authorization required but not provided")

        req.status = ExceptionalAccessRequestStatus.APPROVED
        req.approved_by_user_id = approver_user_id
        req.approved_at = datetime.utcnow()
        req.starts_at = starts_at or datetime.utcnow()
        req.expires_at = expires_at
        req.version = str(int(req.version) + 1)

        grant = ExceptionalAccessGrant(
            id=str(uuid.uuid4()),
            request_id=request_id,
            grantee_user_id=req.requester_user_id,
            resource_type=req.resource_type,
            resource_id=req.resource_id,
            scope_type=req.scope_type,
            granted_at=datetime.utcnow(),
            expires_at=expires_at,
            status=GrantStatus.ACTIVE,
        )
        self.db.add(grant)
        await self.db.flush()
        await self._audit_request(req, "exceptional_access_request_approved", approver_user_id)
        return req, grant

    async def reject_request(
        self,
        request_id: str,
        rejecter_user_id: str,
        rejection_reason: str
    ) -> ExceptionalAccessRequest:
        result = await self.db.execute(
            select(ExceptionalAccessRequest).where(
                and_(
                    ExceptionalAccessRequest.id == request_id,
                    ExceptionalAccessRequest.deleted_at == None
                )
            )
        )
        req = result.scalar_one_or_none()
        if not req:
            raise HTTPException(status_code=404, detail="Request not found")
        if req.status not in (ExceptionalAccessRequestStatus.REQUESTED, ExceptionalAccessRequestStatus.PENDING_PATIENT_AUTHORIZATION):
            raise HTTPException(status_code=409, detail=f"Cannot reject request in status={req.status}")

        req.status = ExceptionalAccessRequestStatus.REJECTED
        req.rejected_by_user_id = rejecter_user_id
        req.rejected_at = datetime.utcnow()
        req.rejection_reason = rejection_reason
        req.version = str(int(req.version) + 1)
        await self.db.flush()
        await self._audit_request(req, "exceptional_access_request_rejected", rejecter_user_id)
        return req

    async def revoke_grant(self, grant_id: str, revoker_user_id: str, reason: str) -> ExceptionalAccessGrant:
        result = await self.db.execute(
            select(ExceptionalAccessGrant).where(
                and_(
                    ExceptionalAccessGrant.id == grant_id,
                    ExceptionalAccessGrant.deleted_at == None
                )
            )
        )
        grant = result.scalar_one_or_none()
        if not grant:
            raise HTTPException(status_code=404, detail="Grant not found")
        if grant.status != GrantStatus.ACTIVE:
            raise HTTPException(status_code=409, detail="Grant is not active")

        grant.status = GrantStatus.REVOKED
        grant.version = str(int(grant.version) + 1)

        # Also revoke the request
        req_result = await self.db.execute(
            select(ExceptionalAccessRequest).where(
                and_(
                    ExceptionalAccessRequest.id == grant.request_id,
                    ExceptionalAccessRequest.deleted_at == None
                )
            )
        )
        req = req_result.scalar_one_or_none()
        if req:
            req.status = ExceptionalAccessRequestStatus.REVOKED
            req.revoked_by_user_id = revoker_user_id
            req.revoked_at = datetime.utcnow()
            req.revoke_reason = reason
            req.version = str(int(req.version) + 1)

        await self.db.flush()
        await self._audit_grant(grant, "exceptional_grant_revoked", revoker_user_id, reason)
        return grant

    async def get_request(self, request_id: str) -> Optional[ExceptionalAccessRequest]:
        result = await self.db.execute(
            select(ExceptionalAccessRequest).where(
                and_(
                    ExceptionalAccessRequest.id == request_id,
                    ExceptionalAccessRequest.deleted_at == None
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_requests(
        self,
        status_filter: Optional[str] = None,
        requester_user_id: Optional[str] = None
    ) -> List[ExceptionalAccessRequest]:
        query = select(ExceptionalAccessRequest).where(
            ExceptionalAccessRequest.deleted_at == None
        )
        if status_filter:
            query = query.where(ExceptionalAccessRequest.status == status_filter)
        if requester_user_id:
            query = query.where(ExceptionalAccessRequest.requester_user_id == requester_user_id)
        query = query.order_by(ExceptionalAccessRequest.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def _audit_request(self, req: ExceptionalAccessRequest, action: str, user_id: str):
        event = AuditEvent(
            id=str(uuid.uuid4()),
            actor_user_id=user_id,
            action=action,
            entity_type="exceptional_access_request",
            entity_id=req.id,
            severity=Severity.INFO,
            before_json=json.dumps({
                "resource_type": req.resource_type,
                "status": req.status,
                "patient_id": req.patient_id
            }),
            created_at=datetime.utcnow()
        )
        self.db.add(event)

    async def _audit_grant(self, grant: ExceptionalAccessGrant, action: str, user_id: str, reason: str):
        event = AuditEvent(
            id=str(uuid.uuid4()),
            actor_user_id=user_id,
            action=action,
            entity_type="exceptional_access_grant",
            entity_id=grant.id,
            severity=Severity.INFO,
            before_json=json.dumps({
                "resource_type": grant.resource_type,
                "reason": reason
            }),
            created_at=datetime.utcnow()
        )
        self.db.add(event)


# =============================================================================
# 5. Clinical Access Logging Service
# =============================================================================

class ClinicalAccessLoggingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_access(
        self,
        actor_user_id: str,
        actor_role_code: str,
        resource_type: str,
        resource_id: Optional[str],
        access_mode: str,
        action: str,
        decision: str,
        patient_id: Optional[str] = None,
        target_user_id: Optional[str] = None,
        policy_snapshot: Optional[Dict] = None,
        exceptional_access_request_id: Optional[str] = None,
        justification: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> ClinicalAccessLog:
        log = ClinicalAccessLog(
            id=str(uuid.uuid4()),
            actor_user_id=actor_user_id,
            actor_role_code=actor_role_code,
            patient_id=patient_id,
            target_user_id=target_user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            access_mode=access_mode,
            action=action,
            decision=decision,
            policy_snapshot_json=json.dumps(policy_snapshot) if policy_snapshot else None,
            exceptional_access_request_id=exceptional_access_request_id,
            justification=justification,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            created_at=datetime.utcnow()
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def get_logs(
        self,
        actor_user_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[ClinicalAccessLog]:
        query = select(ClinicalAccessLog)
        if actor_user_id:
            query = query.where(ClinicalAccessLog.actor_user_id == actor_user_id)
        if patient_id:
            query = query.where(ClinicalAccessLog.patient_id == patient_id)
        if resource_type:
            query = query.where(ClinicalAccessLog.resource_type == resource_type)
        if from_date:
            query = query.where(ClinicalAccessLog.created_at >= from_date)
        if to_date:
            query = query.where(ClinicalAccessLog.created_at <= to_date)
        query = query.order_by(ClinicalAccessLog.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def export_meta(
        self,
        actor_user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Export metadata only - no clinical content."""
        logs = await self.get_logs(
            actor_user_id=actor_user_id,
            resource_type=resource_type,
            from_date=from_date,
            to_date=to_date,
            limit=1000
        )
        return [
            {
                "id": log.id,
                "actor_user_id": log.actor_user_id,
                "actor_role_code": log.actor_role_code,
                "patient_id": log.patient_id,
                "target_user_id": log.target_user_id,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "access_mode": log.access_mode,
                "action": log.action,
                "decision": log.decision,
                "exceptional_access_request_id": log.exceptional_access_request_id,
                "created_at": log.created_at.isoformat() if log.created_at else None,
                # NO content fields
            }
            for log in logs
        ]


# =============================================================================
# 6. Privacy Policy Service
# =============================================================================

class PrivacyPolicyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_policy(
        self,
        policy_type: str,
        version_code: str,
        content_markdown: str
    ) -> PrivacyPolicyVersion:
        # Check for duplicate
        existing = await self.db.execute(
            select(PrivacyPolicyVersion).where(
                and_(
                    PrivacyPolicyVersion.policy_type == policy_type,
                    PrivacyPolicyVersion.version_code == version_code,
                    PrivacyPolicyVersion.deleted_at == None
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Policy version already exists")

        policy = PrivacyPolicyVersion(
            id=str(uuid.uuid4()),
            policy_type=policy_type,
            version_code=version_code,
            content_markdown=content_markdown,
            is_active=False,
        )
        self.db.add(policy)
        await self.db.flush()
        await self._audit("privacy_policy_created", policy.id, {"policy_type": policy_type})
        return policy

    async def publish_policy(self, policy_id: str) -> PrivacyPolicyVersion:
        result = await self.db.execute(
            select(PrivacyPolicyVersion).where(
                and_(
                    PrivacyPolicyVersion.id == policy_id,
                    PrivacyPolicyVersion.deleted_at == None
                )
            )
        )
        policy = result.scalar_one_or_none()
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")

        # Mark current active policy of same type as superseded
        current_active = await self.db.execute(
            select(PrivacyPolicyVersion).where(
                and_(
                    PrivacyPolicyVersion.policy_type == policy.policy_type,
                    PrivacyPolicyVersion.is_active == True,
                    PrivacyPolicyVersion.deleted_at == None
                )
            )
        )
        for old in current_active.scalars().all():
            old.is_active = False

        policy.is_active = True
        policy.published_at = datetime.utcnow()
        policy.version = str(int(policy.version) + 1)
        await self.db.flush()
        await self._audit("privacy_policy_published", policy.id, {"policy_type": policy.policy_type})
        return policy

    async def list_policies(self, policy_type: Optional[str] = None) -> List[PrivacyPolicyVersion]:
        query = select(PrivacyPolicyVersion).where(
            PrivacyPolicyVersion.deleted_at == None
        )
        if policy_type:
            query = query.where(PrivacyPolicyVersion.policy_type == policy_type)
        query = query.order_by(PrivacyPolicyVersion.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_active_policies(self) -> List[PrivacyPolicyVersion]:
        result = await self.db.execute(
            select(PrivacyPolicyVersion).where(
                and_(
                    PrivacyPolicyVersion.is_active == True,
                    PrivacyPolicyVersion.deleted_at == None
                )
            )
        )
        return list(result.scalars().all())

    async def accept_policy(
        self,
        policy_version_id: str,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> PrivacyPolicyAcceptance:
        acceptance = PrivacyPolicyAcceptance(
            id=str(uuid.uuid4()),
            policy_version_id=policy_version_id,
            user_id=user_id,
            accepted_at=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
            status=AcceptanceStatus.ACCEPTED,
        )
        self.db.add(acceptance)
        await self.db.flush()
        return acceptance

    async def _audit(self, action: str, resource_id: str, metadata: Dict):
        event = AuditEvent(
            id=str(uuid.uuid4()),
            user_id="system",
            action=action,
            resource_type="privacy_policy_version",
            resource_id=resource_id,
            severity=Severity.INFO,
            metadata_json=json.dumps(metadata),
            created_at=datetime.utcnow()
        )
        self.db.add(event)


# =============================================================================
# 7. Retention Policy Service
# =============================================================================

class RetentionPolicyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_policy(
        self,
        code: str,
        resource_type: str,
        delete_mode: str,
        retention_days: Optional[int] = None,
        archive_after_days: Optional[int] = None,
        description: Optional[str] = None
    ) -> RetentionPolicy:
        policy = RetentionPolicy(
            id=str(uuid.uuid4()),
            code=code,
            resource_type=resource_type,
            retention_days=retention_days,
            archive_after_days=archive_after_days,
            delete_mode=delete_mode,
            description=description,
            is_active=True,
        )
        self.db.add(policy)
        await self.db.flush()
        await self._audit("retention_policy_created", policy.id, {"resource_type": resource_type})
        return policy

    async def update_policy(
        self,
        policy_id: str,
        retention_days: Optional[int] = None,
        archive_after_days: Optional[int] = None,
        description: Optional[str] = None
    ) -> RetentionPolicy:
        result = await self.db.execute(
            select(RetentionPolicy).where(
                and_(
                    RetentionPolicy.id == policy_id,
                    RetentionPolicy.deleted_at == None
                )
            )
        )
        policy = result.scalar_one_or_none()
        if not policy:
            raise HTTPException(status_code=404, detail="Retention policy not found")

        if retention_days is not None:
            policy.retention_days = retention_days
        if archive_after_days is not None:
            policy.archive_after_days = archive_after_days
        if description is not None:
            policy.description = description
        policy.version = str(int(policy.version) + 1)
        await self.db.flush()
        await self._audit("retention_policy_updated", policy.id, {"resource_type": policy.resource_type})
        return policy

    async def get_policy(self, policy_id: str) -> Optional[RetentionPolicy]:
        result = await self.db.execute(
            select(RetentionPolicy).where(
                and_(
                    RetentionPolicy.id == policy_id,
                    RetentionPolicy.deleted_at == None
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_policy_for_resource(self, resource_type: str) -> Optional[RetentionPolicy]:
        result = await self.db.execute(
            select(RetentionPolicy).where(
                and_(
                    RetentionPolicy.resource_type == resource_type,
                    RetentionPolicy.is_active == True,
                    RetentionPolicy.deleted_at == None
                )
            ).limit(1)
        )
        return result.scalar_one_or_none()

    async def list_policies(self) -> List[RetentionPolicy]:
        result = await self.db.execute(
            select(RetentionPolicy).where(
                and_(
                    RetentionPolicy.is_active == True,
                    RetentionPolicy.deleted_at == None
                )
            )
        )
        return list(result.scalars().all())

    async def _audit(self, action: str, resource_id: str, metadata: Dict):
        event = AuditEvent(
            id=str(uuid.uuid4()),
            user_id="system",
            action=action,
            resource_type="retention_policy",
            resource_id=resource_id,
            severity=Severity.INFO,
            metadata_json=json.dumps(metadata),
            created_at=datetime.utcnow()
        )
        self.db.add(event)


# =============================================================================
# 8. Privacy Incident Service
# =============================================================================

class PrivacyIncidentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_incident(
        self,
        incident_type: str,
        description: str,
        severity: str,
        detected_at: datetime,
        reported_by_user_id: Optional[str] = None,
        affected_resource_type: Optional[str] = None,
        affected_resource_id: Optional[str] = None
    ) -> PrivacyIncident:
        incident = PrivacyIncident(
            id=str(uuid.uuid4()),
            incident_code=f"INC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}",
            detected_at=detected_at,
            reported_by_user_id=reported_by_user_id,
            severity=severity,
            incident_type=incident_type,
            description=description,
            affected_resource_type=affected_resource_type,
            affected_resource_id=affected_resource_id,
            status=IncidentStatus.OPEN,
        )
        self.db.add(incident)
        await self.db.flush()
        await self._add_event(incident.id, IncidentEventType.OPENED, "system", {
            "incident_type": incident_type,
            "severity": severity
        })
        await self._audit("privacy_incident_created", incident.id, reported_by_user_id or "system")
        return incident

    async def assign_incident(self, incident_id: str, admin_id: str) -> PrivacyIncident:
        result = await self.db.execute(
            select(PrivacyIncident).where(
                and_(
                    PrivacyIncident.id == incident_id,
                    PrivacyIncident.deleted_at == None
                )
            )
        )
        incident = result.scalar_one_or_none()
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        if incident.status not in (IncidentStatus.OPEN, IncidentStatus.UNDER_REVIEW):
            raise HTTPException(status_code=409, detail="Cannot assign incident in current status")

        incident.status = IncidentStatus.UNDER_REVIEW
        incident.assigned_admin_id = admin_id
        incident.version = str(int(incident.version) + 1)
        await self.db.flush()
        await self._add_event(incident.id, IncidentEventType.ASSIGNED, admin_id, {"assigned_to": admin_id})
        return incident

    async def contain_incident(self, incident_id: str, admin_id: str) -> PrivacyIncident:
        result = await self.db.execute(
            select(PrivacyIncident).where(
                and_(
                    PrivacyIncident.id == incident_id,
                    PrivacyIncident.deleted_at == None
                )
            )
        )
        incident = result.scalar_one_or_none()
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        if incident.status != IncidentStatus.UNDER_REVIEW:
            raise HTTPException(status_code=409, detail="Incident must be under_review to contain")

        incident.status = IncidentStatus.CONTAINED
        incident.version = str(int(incident.version) + 1)
        await self.db.flush()
        await self._add_event(incident.id, IncidentEventType.CONTAINED, admin_id, {})
        return incident

    async def resolve_incident(
        self,
        incident_id: str,
        admin_id: str,
        resolution_summary: str
    ) -> PrivacyIncident:
        result = await self.db.execute(
            select(PrivacyIncident).where(
                and_(
                    PrivacyIncident.id == incident_id,
                    PrivacyIncident.deleted_at == None
                )
            )
        )
        incident = result.scalar_one_or_none()
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        if incident.status not in (IncidentStatus.UNDER_REVIEW, IncidentStatus.CONTAINED):
            raise HTTPException(status_code=409, detail="Cannot resolve incident in current status")

        incident.status = IncidentStatus.RESOLVED
        incident.resolution_summary = resolution_summary
        incident.resolved_at = datetime.utcnow()
        incident.version = str(int(incident.version) + 1)
        await self.db.flush()
        await self._add_event(incident.id, IncidentEventType.RESOLVED, admin_id, {"summary": resolution_summary})
        await self._audit("privacy_incident_resolved", incident.id, admin_id)
        return incident

    async def dismiss_incident(self, incident_id: str, admin_id: str) -> PrivacyIncident:
        result = await self.db.execute(
            select(PrivacyIncident).where(
                and_(
                    PrivacyIncident.id == incident_id,
                    PrivacyIncident.deleted_at == None
                )
            )
        )
        incident = result.scalar_one_or_none()
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        if incident.status != IncidentStatus.UNDER_REVIEW:
            raise HTTPException(status_code=409, detail="Only under_review incidents can be dismissed")

        incident.status = IncidentStatus.DISMISSED
        incident.version = str(int(incident.version) + 1)
        await self.db.flush()
        await self._add_event(incident.id, IncidentEventType.DISMISSED, admin_id, {})
        return incident

    async def list_incidents(
        self,
        status_filter: Optional[str] = None,
        severity: Optional[str] = None
    ) -> List[PrivacyIncident]:
        query = select(PrivacyIncident).where(
            PrivacyIncident.deleted_at == None
        )
        if status_filter:
            query = query.where(PrivacyIncident.status == status_filter)
        if severity:
            query = query.where(PrivacyIncident.severity == severity)
        query = query.order_by(PrivacyIncident.detected_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_incident(self, incident_id: str) -> Optional[PrivacyIncident]:
        result = await self.db.execute(
            select(PrivacyIncident).where(
                and_(
                    PrivacyIncident.id == incident_id,
                    PrivacyIncident.deleted_at == None
                )
            )
        )
        return result.scalar_one_or_none()

    async def _add_event(
        self,
        incident_id: str,
        event_type: str,
        user_id: str,
        payload: Dict[str, Any]
    ):
        event = PrivacyIncidentEvent(
            id=str(uuid.uuid4()),
            privacy_incident_id=incident_id,
            event_type=event_type,
            event_payload_json=json.dumps(payload),
            created_by_user_id=user_id,
            created_at=datetime.utcnow()
        )
        self.db.add(event)
        await self.db.flush()

    async def _audit(self, action: str, resource_id: str, user_id: str):
        event = AuditEvent(
            id=str(uuid.uuid4()),
            user_id=user_id,
            action=action,
            resource_type="privacy_incident",
            resource_id=resource_id,
            severity=Severity.WARNING,
            created_at=datetime.utcnow()
        )
        self.db.add(event)


# =============================================================================
# 9. Processing Activity Service
# =============================================================================

class ProcessingActivityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        code: str,
        module_name: str,
        purpose: str,
        data_categories: List[str],
        subject_categories: List[str],
        legal_basis: Optional[str] = None,
        retention_policy_id: Optional[str] = None,
        is_sensitive: bool = True
    ) -> ProcessingActivity:
        activity = ProcessingActivity(
            id=str(uuid.uuid4()),
            code=code,
            module_name=module_name,
            purpose=purpose,
            data_categories_json=json.dumps(data_categories),
            subject_categories_json=json.dumps(subject_categories),
            legal_basis=legal_basis,
            retention_policy_id=retention_policy_id,
            is_sensitive=is_sensitive,
            is_active=True,
        )
        self.db.add(activity)
        await self.db.flush()
        await self._audit("processing_activity_created", activity.id, {"module": module_name})
        return activity

    async def update(
        self,
        activity_id: str,
        purpose: Optional[str] = None,
        legal_basis: Optional[str] = None,
        is_sensitive: Optional[bool] = None
    ) -> ProcessingActivity:
        result = await self.db.execute(
            select(ProcessingActivity).where(
                and_(
                    ProcessingActivity.id == activity_id,
                    ProcessingActivity.deleted_at == None
                )
            )
        )
        activity = result.scalar_one_or_none()
        if not activity:
            raise HTTPException(status_code=404, detail="Processing activity not found")
        if purpose is not None:
            activity.purpose = purpose
        if legal_basis is not None:
            activity.legal_basis = legal_basis
        if is_sensitive is not None:
            activity.is_sensitive = is_sensitive
        activity.version = str(int(activity.version) + 1)
        await self.db.flush()
        await self._audit("processing_activity_updated", activity.id, {})
        return activity

    async def list_activities(self) -> List[ProcessingActivity]:
        result = await self.db.execute(
            select(ProcessingActivity).where(
                and_(
                    ProcessingActivity.is_active == True,
                    ProcessingActivity.deleted_at == None
                )
            )
        )
        return list(result.scalars().all())

    async def _audit(self, action: str, resource_id: str, metadata: Dict):
        event = AuditEvent(
            id=str(uuid.uuid4()),
            user_id="system",
            action=action,
            resource_type="processing_activity",
            resource_id=resource_id,
            severity=Severity.INFO,
            metadata_json=json.dumps(metadata),
            created_at=datetime.utcnow()
        )
        self.db.add(event)
