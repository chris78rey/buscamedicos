import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from app.core.database import Base
from app.models import *

async def seed():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        roles = [
            Role(id="role_super_admin", code="super_admin", name="Super Admin", description="Full system access", is_system=True),
            Role(id="role_admin_validation", code="admin_validation", name="Admin Validacion", description="Review professional documents", is_system=True),
            Role(id="role_admin_support", code="admin_support", name="Admin Soporte", description="Support non-clinical access", is_system=True),
            Role(id="role_admin_moderation", code="admin_moderation", name="Admin Moderacion", description="Moderation and sanctions", is_system=True),
            Role(id="role_patient", code="patient", name="Paciente", description="Patient role", is_system=True),
            Role(id="role_professional", code="professional", name="Profesional", description="Health professional role", is_system=True),
            Role(id="role_admin_privacy", code="admin_privacy", name="Admin Privacidad", description="Manage privacy policies and exceptional access", is_system=True),
            Role(id="role_privacy_auditor", code="privacy_auditor", name="Auditor de Privacidad", description="Audit privacy access logs", is_system=True),
            Role(id="role_admin_ops", code="admin_ops", name="Admin Operaciones", description="Operational and deployment management", is_system=True),
        ]
        session.add_all(roles)
        
        agreements = [
            Agreement(
                id="agreement_terms_v1",
                agreement_type=AgreementType.PLATFORM_TERMS,
                version_code="1.0",
                title="Términos y Condiciones de Plataforma",
                content_markdown="# Términos y Condiciones\n\nBienvenido a BuscaMedicos...",
                is_active=True
            ),
            Agreement(
                id="agreement_privacy_v1",
                agreement_type=AgreementType.PRIVACY_POLICY,
                version_code="1.0",
                title="Política de Privacidad",
                content_markdown="# Política de Privacidad\n\nEn BuscaMedicos...",
                is_active=True
            ),
            Agreement(
                id="agreement_professional_v1",
                agreement_type=AgreementType.PROFESSIONAL_RESPONSIBILITY_AGREEMENT,
                version_code="1.0",
                title="Acuerdo de Responsabilidad Profesional",
                content_markdown="# Acuerdo de Responsabilidad Profesional\n\nEl profesional...",
                is_active=True
            ),
        ]
        session.add_all(agreements)
        
        from app.models.step2_models import Specialty, ServiceModality, FeatureFlag as FF
        from app.models.step3_models import PricingPolicy
        
        pricing_policy = PricingPolicy(
            id="policy_default_15",
            code="default_percentage_15",
            name="Default 15% Commission",
            commission_type="percentage",
            commission_value="15.00",
            is_active=True
        )
        session.add(pricing_policy)
        
        specialties = [
            Specialty(id="spec_general", code="general_medicine", name="Medicina General"),
            Specialty(id="spec_pediatrics", code="pediatrics", name="Pediatría"),
            Specialty(id="spec_gynecology", code="gynecology", name="Ginecología"),
            Specialty(id="spec_cardiology", code="cardiology", name="Cardiología"),
            Specialty(id="spec_dermatology", code="dermatology", name="Dermatología"),
            Specialty(id="spec_orthopedics", code="orthopedics", name="Ortopedía"),
        ]
        session.add_all(specialties)
        
        modalities = [
            ServiceModality(id="mod_in_person", code="in_person_consultorio", name="Consulta en Consultorio"),
            ServiceModality(id="mod_tele", code="teleconsulta", name="Teleconsulta"),
        ]
        session.add_all(modalities)
        
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
            FF(id="ff_e2e_smoke", code="e2e_smoke_enabled", enabled="false", description="Enable E2E smoke tests"),
        ]
        session.add_all(feature_flags)
        
        from app.models.step7_models import (
            DataClassification, ClassificationCode,
            ResourceAccessPolicy, AccessMode,
        )
        
        classifications = [
            DataClassification(id="dc_public", code=ClassificationCode.PUBLIC, name="Publico", description="Informacion publica", severity_level=1, is_active=True),
            DataClassification(id="dc_internal", code=ClassificationCode.INTERNAL, name="Interno", description="Informacion interna", severity_level=2, is_active=True),
            DataClassification(id="dc_personal", code=ClassificationCode.PERSONAL, name="Personal", description="Datos personales", severity_level=3, is_active=True),
            DataClassification(id="dc_sensitive", code=ClassificationCode.SENSITIVE_HEALTH, name="Salud Sensible", description="Datos sensibles de salud", severity_level=4, is_active=True),
            DataClassification(id="dc_legal", code=ClassificationCode.RESTRICTED_LEGAL, name="Restringido Legal", description="Datos legalmente restringidos", severity_level=5, is_active=True),
        ]
        session.add_all(classifications)
        
        resource_policies = [
            ResourceAccessPolicy(id="rp_clinical_note", resource_type="clinical_note", classification_code=ClassificationCode.SENSITIVE_HEALTH, access_mode=AccessMode.EXCEPTIONAL_ONLY, requires_relationship=True, requires_patient_authorization=True, requires_justification=True, allow_download=False, is_active=True),
            ResourceAccessPolicy(id="rp_prescription", resource_type="prescription", classification_code=ClassificationCode.SENSITIVE_HEALTH, access_mode=AccessMode.HYBRID, requires_relationship=True, requires_patient_authorization=False, requires_justification=False, allow_download=True, is_active=True),
            ResourceAccessPolicy(id="rp_care_instruction", resource_type="care_instruction", classification_code=ClassificationCode.SENSITIVE_HEALTH, access_mode=AccessMode.HYBRID, requires_relationship=True, requires_patient_authorization=False, requires_justification=False, allow_download=True, is_active=True),
            ResourceAccessPolicy(id="rp_clinical_file", resource_type="clinical_file", classification_code=ClassificationCode.SENSITIVE_HEALTH, access_mode=AccessMode.EXCEPTIONAL_ONLY, requires_relationship=True, requires_patient_authorization=True, allow_download=False, is_active=True),
            ResourceAccessPolicy(id="rp_exam_result", resource_type="exam_result", classification_code=ClassificationCode.SENSITIVE_HEALTH, access_mode=AccessMode.HYBRID, requires_relationship=True, requires_patient_authorization=False, allow_download=True, is_active=True),
            ResourceAccessPolicy(id="rp_exam_result_file", resource_type="exam_result_file", classification_code=ClassificationCode.SENSITIVE_HEALTH, access_mode=AccessMode.HYBRID, requires_relationship=True, requires_patient_authorization=False, allow_download=True, is_active=True),
            ResourceAccessPolicy(id="rp_teleconsultation_meta", resource_type="teleconsultation_meta", classification_code=ClassificationCode.PERSONAL, access_mode=AccessMode.HYBRID, requires_relationship=True, is_active=True),
            ResourceAccessPolicy(id="rp_appointment_meta", resource_type="appointment_meta", classification_code=ClassificationCode.INTERNAL, access_mode=AccessMode.NORMAL, requires_relationship=False, is_active=True),
        ]
        session.add_all(resource_policies)
        
        from app.models.step8_models import OperationalJob, JobType
        
        operational_jobs = [
            OperationalJob(id="job_backup_db", job_code="backup_db", job_type=JobType.BACKUP_DB, schedule_cron="0 2 * * *", is_active=True),
            OperationalJob(id="job_backup_files", job_code="backup_files", job_type=JobType.BACKUP_FILES, schedule_cron="0 3 * * *", is_active=True),
            OperationalJob(id="job_cleanup_temp", job_code="cleanup_temp", job_type=JobType.CLEANUP_TEMP, schedule_cron="0 4 * * *", is_active=True),
            OperationalJob(id="job_expire_access", job_code="expire_access", job_type=JobType.EXPIRE_ACCESS, schedule_cron="0 5 * * *", is_active=True),
            OperationalJob(id="job_rotate_logs", job_code="rotate_logs", job_type=JobType.ROTATE_LOGS, schedule_cron="0 0 * * *", is_active=True),
            OperationalJob(id="job_restore_test", job_code="restore_test", job_type=JobType.RESTORE_TEST, schedule_cron="0 6 * * 0", is_active=True),
        ]
        session.add_all(operational_jobs)
        
        await session.commit()
        print("Seed completed")

if __name__ == "__main__":
    asyncio.run(seed())