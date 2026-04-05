import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import settings
from app.core.security import hash_password
from app.models import *
from app.models.step2_models import Specialty, ServiceModality
from app.models.step3_models import PricingPolicy
from app.models.step8_models import OperationalJob, JobType
from app.models.system import FeatureFlag as FF


async def _add_if_missing(session: AsyncSession, model, entity_id: str, entity):
    existing = await session.get(model, entity_id)
    if not existing:
        session.add(entity)


async def _get_role_by_code(session: AsyncSession, code: str):
    result = await session.execute(select(Role).where(Role.code == code))
    return result.scalar_one_or_none()


async def seed():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        roles = [
            Role(
                id="role_super_admin",
                code="super_admin",
                name="Super Admin",
                description="Full system access",
                is_system=True,
            ),
            Role(
                id="role_admin_validation",
                code="admin_validation",
                name="Admin Validacion",
                description="Review professional documents",
                is_system=True,
            ),
            Role(
                id="role_admin_support",
                code="admin_support",
                name="Admin Soporte",
                description="Support non-clinical access",
                is_system=True,
            ),
            Role(
                id="role_admin_moderation",
                code="admin_moderation",
                name="Admin Moderacion",
                description="Moderation and sanctions",
                is_system=True,
            ),
            Role(
                id="role_patient",
                code="patient",
                name="Paciente",
                description="Patient role",
                is_system=True,
            ),
            Role(
                id="role_professional",
                code="professional",
                name="Profesional",
                description="Health professional role",
                is_system=True,
            ),
            Role(
                id="role_admin_privacy",
                code="admin_privacy",
                name="Admin Privacidad",
                description="Manage privacy policies and exceptional access",
                is_system=True,
            ),
            Role(
                id="role_privacy_auditor",
                code="privacy_auditor",
                name="Auditor de Privacidad",
                description="Audit privacy access logs",
                is_system=True,
            ),
            Role(
                id="role_admin_ops",
                code="admin_ops",
                name="Admin Operaciones",
                description="Operational and deployment management",
                is_system=True,
            ),
        ]

        for role in roles:
            await _add_if_missing(session, Role, role.id, role)

        agreements = [
            Agreement(
                id="agreement_terms_v1",
                agreement_type=AgreementType.PLATFORM_TERMS,
                version_code="1.0",
                title="Términos y Condiciones de Plataforma",
                content_markdown="# Términos y Condiciones\n\nBienvenido a BuscaMedicos...",
                is_active=True,
                created_by="seed",
                updated_by="seed",
            ),
            Agreement(
                id="agreement_privacy_v1",
                agreement_type=AgreementType.PRIVACY_POLICY,
                version_code="1.0",
                title="Política de Privacidad",
                content_markdown="# Política de Privacidad\n\nEn BuscaMedicos...",
                is_active=True,
                created_by="seed",
                updated_by="seed",
            ),
            Agreement(
                id="agreement_professional_v1",
                agreement_type=AgreementType.PROFESSIONAL_RESPONSIBILITY_AGREEMENT,
                version_code="1.0",
                title="Acuerdo de Responsabilidad Profesional",
                content_markdown="# Acuerdo de Responsabilidad Profesional\n\nEl profesional...",
                is_active=True,
                created_by="seed",
                updated_by="seed",
            ),
        ]

        for agreement in agreements:
            await _add_if_missing(session, Agreement, agreement.id, agreement)

        pricing_policy = PricingPolicy(
            id="policy_default_15",
            code="default_percentage_15",
            name="Default 15% Commission",
            commission_type="percentage",
            commission_value="15.00",
            is_active=True,
        )
        await _add_if_missing(session, PricingPolicy, pricing_policy.id, pricing_policy)

        specialties = [
            Specialty(id="spec_general", code="general_medicine", name="Medicina General"),
            Specialty(id="spec_pediatrics", code="pediatrics", name="Pediatría"),
            Specialty(id="spec_gynecology", code="gynecology", name="Ginecología"),
            Specialty(id="spec_cardiology", code="cardiology", name="Cardiología"),
            Specialty(id="spec_dermatology", code="dermatology", name="Dermatología"),
            Specialty(id="spec_orthopedics", code="orthopedics", name="Ortopedía"),
        ]
        for specialty in specialties:
            await _add_if_missing(session, Specialty, specialty.id, specialty)

        modalities = [
            ServiceModality(
                id="mod_in_person",
                code="in_person_consultorio",
                name="Consulta en Consultorio",
            ),
            ServiceModality(
                id="mod_tele",
                code="teleconsulta",
                name="Teleconsulta",
            ),
        ]
        for modality in modalities:
            await _add_if_missing(session, ServiceModality, modality.id, modality)

        feature_flags = [
            FF(id="ff_teleconsulta", code="teleconsulta_enabled", enabled="true", description="Enable teleconsulta feature"),
            FF(id="ff_pagos", code="pagos_enabled", enabled="true", description="Enable pagos feature"),
            FF(id="ff_public_profiles", code="public_profiles_enabled", enabled="true", description="Enable public professional profiles"),
            FF(id="ff_appointments", code="appointments_enabled", enabled="true", description="Enable appointments feature"),
            FF(id="ff_refunds", code="refunds_enabled", enabled="true", description="Enable refunds feature"),
            FF(id="ff_settlements", code="settlements_enabled", enabled="true", description="Enable settlements feature"),
            FF(id="ff_teleconsultation_enabled", code="teleconsultation_enabled", enabled="true", description="Enable teleconsultation sessions"),
            FF(id="ff_prescriptions_enabled", code="prescriptions_enabled", enabled="true", description="Enable prescription feature"),
            FF(id="ff_care_instructions_enabled", code="care_instructions_enabled", enabled="true", description="Enable care instructions feature"),
            FF(id="ff_clinical_simple_notes_enabled", code="clinical_simple_notes_enabled", enabled="true", description="Enable simple clinical notes"),
            FF(id="ff_reviews_enabled", code="reviews_enabled", enabled="true", description="Enable reviews feature"),
            FF(id="ff_reports_enabled", code="reports_enabled", enabled="true", description="Enable safety reports feature"),
            FF(id="ff_moderation_enabled", code="moderation_enabled", enabled="true", description="Enable moderation feature"),
            FF(id="ff_sanctions_enabled", code="sanctions_enabled", enabled="true", description="Enable sanctions feature"),
            FF(id="ff_privacy_hardening", code="privacy_hardening_enabled", enabled="true", description="Enable privacy hardening"),
            FF(id="ff_exceptional_access", code="exceptional_access_enabled", enabled="true", description="Enable exceptional access requests"),
            FF(id="ff_retention_policies", code="retention_policies_enabled", enabled="true", description="Enable retention policies"),
            FF(id="ff_privacy_incidents", code="privacy_incidents_enabled", enabled="true", description="Enable privacy incidents"),
            FF(id="ff_go_live_guard", code="go_live_guard_enabled", enabled="false", description="Block non-production traffic"),
            FF(id="ff_prod_observability", code="production_observability_enabled", enabled="false", description="Enable production observability"),
            FF(id="ff_automated_backups", code="automated_backups_enabled", enabled="true", description="Enable automated backups"),
            FF(id="ff_restore_test", code="restore_test_enabled", enabled="true", description="Enable restore test jobs"),
            FF(id="ff_rate_limit", code="rate_limit_enabled", enabled="true", description="Enable rate limiting"),
            FF(id="ff_e2e_smoke", code="e2e_smoke_enabled", enabled="true", description="Enable local smoke tests"),
        ]
        for feature_flag in feature_flags:
            await _add_if_missing(session, FF, feature_flag.id, feature_flag)

        operational_jobs = [
            OperationalJob(
                id="job_backup_db",
                job_code="backup_db",
                job_type=JobType.BACKUP_DB,
                schedule_cron="0 2 * * *",
                is_active=True,
            ),
            OperationalJob(
                id="job_backup_files",
                job_code="backup_files",
                job_type=JobType.BACKUP_FILES,
                schedule_cron="0 3 * * *",
                is_active=True,
            ),
            OperationalJob(
                id="job_cleanup_temp",
                job_code="cleanup_temp",
                job_type=JobType.CLEANUP_TEMP,
                schedule_cron="0 4 * * *",
                is_active=True,
            ),
            OperationalJob(
                id="job_expire_access",
                job_code="expire_access",
                job_type=JobType.EXPIRE_ACCESS,
                schedule_cron="0 5 * * *",
                is_active=True,
            ),
            OperationalJob(
                id="job_rotate_logs",
                job_code="rotate_logs",
                job_type=JobType.ROTATE_LOGS,
                schedule_cron="0 0 * * *",
                is_active=True,
            ),
            OperationalJob(
                id="job_restore_test",
                job_code="restore_test",
                job_type=JobType.RESTORE_TEST,
                schedule_cron="0 6 * * 0",
                is_active=True,
            ),
        ]
        for job in operational_jobs:
            await _add_if_missing(session, OperationalJob, job.id, job)

        # superadministrador local
        existing_admin_result = await session.execute(
            select(User).where(User.email == "christian19782013@gmail.com")
        )
        admin_user = existing_admin_result.scalar_one_or_none()

        if not admin_user:
            admin_user = User(
                id="user_super_admin_local",
                email="christian19782013@gmail.com",
                password_hash=hash_password("cr19780302"),
                is_email_verified=True,
                status=UserStatus.ACTIVE,
                created_by="seed",
                updated_by="seed",
            )
            session.add(admin_user)
            await session.flush()

            admin_person = Person(
                id="person_super_admin_local",
                user_id=admin_user.id,
                first_name="Christian",
                last_name="Ruiz",
                national_id="1719780302",
                phone="0999999999",
                country="Ecuador",
                created_by="seed",
                updated_by="seed",
            )
            session.add(admin_person)

            super_admin_role = await _get_role_by_code(session, "super_admin")
            if super_admin_role:
                session.add(
                    UserRole(
                        id="user_role_super_admin_local",
                        user_id=admin_user.id,
                        role_id=super_admin_role.id,
                        assigned_by="seed",
                        status=UserRoleStatus.ACTIVE,
                    )
                )

        await session.commit()
        print("Seed completed")


if __name__ == "__main__":
    asyncio.run(seed())
