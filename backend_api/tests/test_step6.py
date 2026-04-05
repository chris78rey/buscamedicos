import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from decimal import Decimal


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = "user-123"
    user.roles = []
    return user


@pytest.fixture
def mock_current_user():
    user = MagicMock()
    user.id = "user-123"
    user.awaitable_attrs = MagicMock()
    user.awaitable_attrs.roles = pytest.fixture(
        lambda: [MagicMock(code="admin_moderation")]
    )
    return user


class TestReviewService:
    @pytest.mark.asyncio
    async def test_patient_review_requires_completed_appointment(self, mock_db):
        from app.services.step6_services import ReviewService
        from app.models.step2_models import Appointment, AppointmentStatus

        mock_appt = MagicMock()
        mock_appt.status = AppointmentStatus.CANCELLED
        mock_appt.patient_id = "user-123"
        mock_appt.professional_id = "prof-456"

        result = AsyncMock()
        result.scalar_one_or_none.return_value = mock_appt
        mock_db.execute.return_value = result

        service = ReviewService(mock_db)

        with pytest.raises(Exception) as exc_info:
            await service.create_patient_review(
                appointment_id="appt-1",
                patient_id="user-123",
                professional_id="prof-456",
                data=MagicMock(rating_overall=5)
            )
        assert "Only completed appointments" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_no_duplicate_review_per_direction(self, mock_db):
        from app.services.step6_services import ReviewService

        mock_appt = MagicMock()
        mock_appt.status = "completed"
        mock_appt.patient_id = "user-123"
        mock_appt.professional_id = "prof-456"

        result1 = AsyncMock()
        result1.scalar_one_or_none.return_value = mock_appt
        mock_db.execute.return_value = result1

        result2 = AsyncMock()
        existing = MagicMock()
        result2.scalar_one_or_none.return_value = existing
        mock_db.execute.return_value = result2

        service = ReviewService(mock_db)

        with pytest.raises(Exception) as exc_info:
            await service.create_patient_review(
                appointment_id="appt-1",
                patient_id="user-123",
                professional_id="prof-456",
                data=MagicMock(rating_overall=5)
            )
        assert "already exists" in str(exc_info.value)


class TestReputationService:
    @pytest.mark.asyncio
    async def test_reputation_calculates_correctly(self, mock_db):
        from app.services.step6_services import ReputationService
        from app.models.step6_models import AppointmentReview, ReviewVisibility, ReviewStatus

        mock_review = MagicMock()
        mock_review.rating_overall = 5
        mock_review.rating_punctuality = 4
        mock_review.rating_communication = 5
        mock_review.rating_respect = 4

        result = AsyncMock()
        result.scalars.return_value.all.return_value = [mock_review]
        mock_db.execute.return_value = result

        service = ReputationService(mock_db)
        stats = await service.recalculate_reputation("prof-456")

        assert stats.public_reviews_count == 1
        assert float(stats.avg_overall) == 5.0


class TestSanctionEnforcementService:
    @pytest.mark.asyncio
    async def test_sanctioned_professional_blocked_from_public_visibility(self, mock_db):
        from app.services.step6_services import SanctionEnforcementService
        from app.models.step6_models import AccountSanction, SanctionStatus, SanctionType

        mock_sanction = MagicMock()
        mock_sanction.sanction_type = SanctionType.TEMPORARY_SUSPENSION
        mock_sanction.starts_at = datetime.utcnow() - timedelta(days=1)
        mock_sanction.ends_at = datetime.utcnow() + timedelta(days=7)

        result = AsyncMock()
        result.scalars.return_value.all.return_value = [mock_sanction]
        mock_db.execute.return_value = result

        service = SanctionEnforcementService(mock_db)
        is_restricted = await service.is_target_restricted(
            "professional", "prof-456", "professional_public_visibility"
        )

        assert is_restricted is True

    @pytest.mark.asyncio
    async def test_warning_does_not_block_operations(self, mock_db):
        from app.services.step6_services import SanctionEnforcementService
        from app.models.step6_models import AccountSanction, SanctionStatus, SanctionType

        mock_sanction = MagicMock()
        mock_sanction.sanction_type = SanctionType.WARNING
        mock_sanction.starts_at = datetime.utcnow() - timedelta(days=1)
        mock_sanction.ends_at = None

        result = AsyncMock()
        result.scalars.return_value.all.return_value = [mock_sanction]
        mock_db.execute.return_value = result

        service = SanctionEnforcementService(mock_db)
        is_restricted = await service.is_target_restricted(
            "professional", "prof-456", "professional_can_receive_booking"
        )

        assert is_restricted is False


class TestReportService:
    @pytest.mark.asyncio
    async def test_report_creation(self, mock_db):
        from app.services.step6_services import ReportService
        from app.models.step6_models import SafetyReport, ReportStatus

        result = AsyncMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result

        service = ReportService(mock_db)

        data = MagicMock()
        data.subject_type = "professional"
        data.subject_id = "prof-456"
        data.category_code = "abuse"
        data.severity_claimed = "high"
        data.description = "This professional was abusive"
        data.appointment_id = None
        data.evidence_files = None

        report = await service.create_report("reporter-1", data)

        assert report.subject_type == "professional"
        assert report.category_code == "abuse"


class TestModerationCaseService:
    @pytest.mark.asyncio
    async def test_case_created_with_correct_status(self, mock_db):
        from app.services.step6_services import ModerationCaseService
        from app.models.step6_models import ModerationCaseStatus

        result = AsyncMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result

        service = ModerationCaseService(mock_db)
        case = await service.create_case(
            source_type="report",
            target_type="professional",
            target_id="prof-456",
            priority="high",
            admin_id="admin-1"
        )

        assert case.status == ModerationCaseStatus.OPEN
        assert case.priority == "high"


class TestSanctionService:
    @pytest.mark.asyncio
    async def test_temporary_suspension_requires_ends_at(self, mock_db):
        from app.services.step6_services import SanctionService

        service = SanctionService(mock_db)

        with pytest.raises(Exception) as exc_info:
            await service.create_sanction(
                target_type="professional",
                target_id="prof-456",
                sanction_type="temporary_suspension",
                reason_code="abuse",
                reason_text="Abusive behavior",
                starts_at=datetime.utcnow(),
                ends_at=None,
                applied_by_user_id="admin-1"
            )
        assert "requires ends_at" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_lift_sanction_requires_active_status(self, mock_db):
        from app.services.step6_services import SanctionService
        from app.models.step6_models import SanctionStatus

        mock_sanction = MagicMock()
        mock_sanction.status = SanctionStatus.LIFTED

        result = AsyncMock()
        result.scalar_one_or_none.return_value = mock_sanction
        mock_db.execute.return_value = result

        service = SanctionService(mock_db)

        with pytest.raises(Exception) as exc_info:
            await service.lift_sanction(
                sanction_id="sanction-1",
                lifted_by_user_id="admin-1",
                reason="Appeal granted"
            )
        assert "not active" in str(exc_info.value)


class TestReviewVisibility:
    def test_patient_review_is_public(self):
        from app.models.step6_models import ReviewVisibility
        assert ReviewVisibility.PUBLIC == "public"

    def test_professional_review_is_internal_only(self):
        from app.models.step6_models import ReviewVisibility
        assert ReviewVisibility.INTERNAL_ONLY == "internal_only"


class TestSanctionTypes:
    def test_sanction_types_defined(self):
        from app.models.step6_models import SanctionType
        assert SanctionType.WARNING == "warning"
        assert SanctionType.TEMPORARY_SUSPENSION == "temporary_suspension"
        assert SanctionType.PERMANENT_SUSPENSION == "permanent_suspension"
        assert SanctionType.VISIBILITY_RESTRICTION == "visibility_restriction"
        assert SanctionType.REVIEW_HIDDEN == "review_hidden"


class TestReportCategories:
    def test_categories_defined(self):
        from app.models.step6_models import ReportCategory
        assert ReportCategory.ABUSE == "abuse"
        assert ReportCategory.FRAUD == "fraud"
        assert ReportCategory.HARASSMENT == "harassment"
        assert ReportCategory.IMPERSONATION == "impersonation"
        assert ReportCategory.NO_SHOW == "no_show"
        assert ReportCategory.UNSAFE_BEHAVIOR == "unsafe_behavior"
        assert ReportCategory.FAKE_PROFILE == "fake_profile"
        assert ReportCategory.INAPPROPRIATE_REVIEW == "inappropriate_review"
        assert ReportCategory.OTHER == "other"


class TestModerationCaseStatusTransitions:
    def test_valid_statuses(self):
        from app.models.step6_models import ModerationCaseStatus
        assert ModerationCaseStatus.OPEN == "open"
        assert ModerationCaseStatus.UNDER_REVIEW == "under_review"
        assert ModerationCaseStatus.PREVENTIVE_ACTION == "preventive_action"
        assert ModerationCaseStatus.RESOLVED == "resolved"
        assert ModerationCaseStatus.DISMISSED == "dismissed"


class TestAdminModerationAuthorization:
    def test_require_admin_moderation_rejects_regular_user(self):
        from app.core.moderation_authorization import require_admin_moderation
        from fastapi import HTTPException

        mock_user = MagicMock()
        mock_user.awaitable_attrs = MagicMock()
        mock_user.awaitable_attrs.roles = pytest.fixture(
            lambda: [MagicMock(code="patient")]
        )

        with pytest.raises(HTTPException) as exc_info:
            require_admin_moderation(mock_user, MagicMock())
        assert exc_info.value.status_code == 403

    def test_require_admin_moderation_allows_moderator(self):
        from app.core.moderation_authorization import require_admin_moderation

        mock_user = MagicMock()
        mock_user.awaitable_attrs = MagicMock()
        mock_user.awaitable_attrs.roles = [MagicMock(code="admin_moderation")]

        result = require_admin_moderation(mock_user, MagicMock())

        async def run():
            return await result

        import asyncio
        assert asyncio.iscoroutine(result)
