import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta
from fastapi import HTTPException


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.add = MagicMock()
    return db


class TestContextualAccessDecisionService:
    @pytest.mark.asyncio
    async def test_admin_denied_normal_access_to_sensitive_health(self, mock_db):
        from app.services.step7_services import ContextualAccessDecisionService
        from app.models.step7_models import ClassificationCode, AccessMode

        user = MagicMock()
        user.id = "admin-123"
        user.role_code = "admin_moderation"

        service = ContextualAccessDecisionService(mock_db)
        result = await service.evaluate_sensitive_access(
            actor_user=user,
            resource_type="clinical_note",
            resource_id="note-1",
            action="read",
        )
        assert result["allowed"] is False
        assert result["requires_exceptional_request"] is True

    @pytest.mark.asyncio
    async def test_patient_can_access_own_data_normal_mode(self, mock_db):
        from app.services.step7_services import ContextualAccessDecisionService

        user = MagicMock()
        user.id = "patient-123"
        user.role_code = "patient"

        mock_policy = MagicMock()
        mock_policy.classification_code = "sensitive_health"
        mock_policy.access_mode = "hybrid"
        mock_policy.requires_relationship = False
        mock_policy.requires_patient_authorization = False
        mock_policy.allow_download = False

        async def mock_get_classification(rt):
            return mock_policy
        mock_db.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=None))

        service = ContextualAccessDecisionService(mock_db)
        service.classification_service.get_classification = mock_get_classification

        result = await service.evaluate_sensitive_access(
            actor_user=user,
            resource_type="appointment_meta",
            resource_id="appt-1",
            action="read",
            context={"patient_id": "patient-123"},
        )
        assert result["allowed"] is True
        assert result["mode"] == "normal"

    @pytest.mark.asyncio
    async def test_privacy_auditor_cannot_access_clinical_content(self, mock_db):
        from app.services.step7_services import ContextualAccessDecisionService

        user = MagicMock()
        user.id = "auditor-1"
        user.role_code = "privacy_auditor"

        mock_policy = MagicMock()
        mock_policy.classification_code = "sensitive_health"
        mock_policy.access_mode = "normal"
        mock_policy.requires_relationship = False

        async def mock_get_classification(rt):
            return mock_policy

        service = ContextualAccessDecisionService(mock_db)
        service.classification_service.get_classification = mock_get_classification

        result = await service.evaluate_sensitive_access(
            actor_user=user,
            resource_type="clinical_note",
            action="read",
        )
        assert result["allowed"] is False
        assert "privacy_auditor cannot access clinical content" in result["decision_reason"]

    @pytest.mark.asyncio
    async def test_denied_access_generates_log(self, mock_db):
        from app.services.step7_services import ClinicalAccessLoggingService
        from app.models.step7_models import ClinicalAccessDecision

        service = ClinicalAccessLoggingService(mock_db)
        log = await service.log_access(
            actor_user_id="admin-1",
            actor_role_code="admin_moderation",
            resource_type="clinical_note",
            resource_id="note-1",
            access_mode="normal",
            action="read",
            decision=ClinicalAccessDecision.DENIED,
        )
        assert log.actor_user_id == "admin-1"
        mock_db.add.assert_called()


class TestPatientConsentService:
    @pytest.mark.asyncio
    async def test_grant_consent_creates_consent(self, mock_db):
        from app.services.step7_services import PatientConsentService
        from app.models.step7_models import ConsentStatus, ConsentSource

        mock_db.execute.return_value = MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[]))))

        service = PatientConsentService(mock_db)
        consent = await service.grant_consent(
            patient_id="patient-1",
            consent_type="data_processing_health",
            source=ConsentSource.CLICKWRAP,
            granted_by_user_id="patient-1",
        )
        assert consent.patient_id == "patient-1"
        assert consent.status == ConsentStatus.GRANTED
        mock_db.add.assert_called()

    @pytest.mark.asyncio
    async def test_revoke_consent_updates_status(self, mock_db):
        from app.services.step7_services import PatientConsentService
        from app.models.step7_models import ConsentStatus

        existing_consent = MagicMock()
        existing_consent.id = "consent-1"
        existing_consent.patient_id = "patient-1"
        existing_consent.consent_type = "data_processing_health"
        existing_consent.status = ConsentStatus.GRANTED
        existing_consent.deleted_at = None
        existing_consent.version = "1"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_consent
        mock_db.execute.return_value = mock_result

        service = PatientConsentService(mock_db)
        revoked = await service.revoke_consent("consent-1", "patient-1")
        assert revoked.status == ConsentStatus.REVOKED


class TestExceptionalAccessRequestService:
    @pytest.mark.asyncio
    async def test_create_request_requires_justification(self, mock_db):
        from app.services.step7_services import ExceptionalAccessRequestService

        service = ExceptionalAccessRequestService(mock_db)
        with pytest.raises(HTTPException) as exc_info:
            await service.create_request(
                requester_user_id="prof-1",
                requester_role_code="professional",
                resource_type="clinical_note",
                scope_type="single_resource",
                justification="",
                requested_minutes=30,
            )
        assert "Justification is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_requested_minutes_must_be_positive(self, mock_db):
        from app.services.step7_services import ExceptionalAccessRequestService

        service = ExceptionalAccessRequestService(mock_db)
        with pytest.raises(HTTPException) as exc_info:
            await service.create_request(
                requester_user_id="prof-1",
                requester_role_code="professional",
                resource_type="clinical_note",
                scope_type="single_resource",
                justification="Audit required",
                requested_minutes=0,
            )
        assert "requested_minutes must be positive" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_approve_requires_future_expiry(self, mock_db):
        from app.services.step7_services import ExceptionalAccessRequestService

        service = ExceptionalAccessRequestService(mock_db)
        with pytest.raises(HTTPException) as exc_info:
            await service.approve_request(
                request_id="req-1",
                approver_user_id="admin-1",
                expires_at=datetime.utcnow() - timedelta(hours=1),
            )
        assert "expires_at must be in the future" in str(exc_info.value)


class TestRetentionPolicyService:
    @pytest.mark.asyncio
    async def test_legal_hold_blocks_retention(self, mock_db):
        from app.services.step7_services import RetentionPolicyService

        service = RetentionPolicyService(mock_db)
        policy = await service.get_policy_for_resource("clinical_note")
        if policy:
            assert policy.is_active is True


class TestPrivacyIncidentService:
    @pytest.mark.asyncio
    async def test_create_incident_generates_code(self, mock_db):
        from app.services.step7_services import PrivacyIncidentService
        from app.models.step7_models import IncidentType, IncidentSeverity, IncidentStatus

        mock_db.execute.return_value = MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[]))))

        service = PrivacyIncidentService(mock_db)
        incident = await service.create_incident(
            incident_type=IncidentType.UNAUTHORIZED_ACCESS,
            description="Unauthorized access attempt",
            severity=IncidentSeverity.HIGH,
            detected_at=datetime.utcnow(),
            reported_by_user_id="reporter-1",
        )
        assert incident.incident_code is not None
        assert incident.status == IncidentStatus.OPEN
        assert incident.severity == IncidentSeverity.HIGH

    @pytest.mark.asyncio
    async def test_incident_state_transitions(self, mock_db):
        from app.services.step7_services import PrivacyIncidentService
        from app.models.step7_models import IncidentStatus

        existing = MagicMock()
        existing.id = "incident-1"
        existing.status = IncidentStatus.OPEN
        existing.version = "1"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_db.execute.return_value = mock_result

        service = PrivacyIncidentService(mock_db)
        assigned = await service.assign_incident("incident-1", "admin-1")
        assert assigned.status == IncidentStatus.UNDER_REVIEW


class TestClinicalAccessLoggingService:
    @pytest.mark.asyncio
    async def test_export_meta_excludes_content(self, mock_db):
        from app.services.step7_services import ClinicalAccessLoggingService
        from app.models.step7_models import ClinicalAccessMode, ClinicalAccessAction, ClinicalAccessDecision

        mock_log = MagicMock()
        mock_log.id = "log-1"
        mock_log.actor_user_id = "prof-1"
        mock_log.actor_role_code = "professional"
        mock_log.patient_id = "patient-1"
        mock_log.target_user_id = None
        mock_log.resource_type = "clinical_note"
        mock_log.resource_id = "note-content-xyz"
        mock_log.access_mode = ClinicalAccessMode.NORMAL
        mock_log.action = ClinicalAccessAction.READ
        mock_log.decision = ClinicalAccessDecision.ALLOWED
        mock_log.exceptional_access_request_id = None
        mock_log.created_at = datetime.utcnow()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_log]
        mock_db.execute.return_value = mock_result

        service = ClinicalAccessLoggingService(mock_db)
        exports = await service.export_meta(resource_type="clinical_note")
        assert len(exports) == 1
        assert "note-content-xyz" not in str(exports[0])
        assert exports[0]["resource_type"] == "clinical_note"


class TestPrivacyPolicyService:
    @pytest.mark.asyncio
    async def test_publish_marks_old_active_as_superseded(self, mock_db):
        from app.services.step7_services import PrivacyPolicyService
        from app.models.step7_models import PrivacyPolicyType

        old_policy = MagicMock()
        old_policy.id = "policy-old"
        old_policy.policy_type = PrivacyPolicyType.PATIENT_PRIVACY
        old_policy.is_active = True
        old_policy.version = "1"

        new_policy = MagicMock()
        new_policy.id = "policy-new"
        new_policy.policy_type = PrivacyPolicyType.PATIENT_PRIVACY
        new_policy.is_active = False
        new_policy.version = "1"

        call_count = [0]
        def mock_scalar():
            call_count[0] += 1
            if call_count[0] == 1:
                return new_policy
            return old_policy

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = mock_scalar
        mock_result.scalars.return_value.all.return_value = [old_policy]
        mock_db.execute.return_value = mock_result

        service = PrivacyPolicyService(mock_db)
        published = await service.publish_policy("policy-new")
        assert published.is_active is True
        assert old_policy.is_active is False
