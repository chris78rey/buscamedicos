import asyncio
import uuid
from datetime import datetime, timedelta, time
from decimal import Decimal
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import settings
from app.core.security import hash_password
from app.models import *
from app.models.step2_models import Specialty, ServiceModality
from app.models.step3_models import PricingPolicy, ProfessionalPrice
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

        # demo dataset for UI (30 professionals, slots, and 10 patient appointments)
        specialty_catalog = [
            ("medicina_general", "Medicina General", "Atención primaria y prevención."),
            ("cardiologia", "Cardiología", "Diagnóstico y tratamiento cardiovascular."),
            ("pediatria", "Pediatría", "Salud integral de niños y adolescentes."),
            ("dermatologia", "Dermatología", "Cuidado de piel, cabello y uñas."),
            ("ginecologia", "Ginecología", "Salud sexual y reproductiva."),
            ("psiquiatria", "Psiquiatría", "Salud mental y acompañamiento clínico."),
            ("traumatologia", "Traumatología", "Lesiones óseas y musculares."),
            ("odontologia", "Odontología", "Salud bucal y estética dental."),
            ("neurologia", "Neurología", "Sistema nervioso y trastornos neurológicos."),
            ("endocrinologia", "Endocrinología", "Trastornos hormonales y metabólicos."),
        ]

        specialty_ids = []
        for code, name, desc in specialty_catalog:
            result = await session.execute(select(Specialty).where(Specialty.code == code))
            specialty = result.scalar_one_or_none()
            if not specialty:
                specialty = Specialty(
                    code=code,
                    name=name,
                    description=desc,
                    is_active=True,
                )
                session.add(specialty)
                await session.flush()
            specialty_ids.append(specialty.id)

        demo_prof_count = 30
        first_names = [
            "Sofía", "Mateo", "Valentina", "Sebastián", "Camila",
            "Daniel", "Isabella", "Alejandro", "Lucía", "Andrés",
        ]
        last_names = [
            "Pérez", "García", "Rodríguez", "López", "Martínez",
            "Gómez", "Ruiz", "Díaz", "Vega", "Morales",
        ]
        titles = [
            "Médico General",
            "Cardiólogo",
            "Pediatra",
            "Dermatólogo",
            "Ginecólogo",
            "Psiquiatra",
            "Traumatólogo",
            "Odontólogo",
            "Neurólogo",
            "Endocrinólogo",
        ]
        cities = ["Quito", "Guayaquil", "Cuenca", "Ambato", "Loja"]
        provinces = ["Pichincha", "Guayas", "Azuay", "Tungurahua", "Loja"]
        bios = [
            "Atención centrada en el paciente y planes personalizados.",
            "Experiencia en consulta privada y telemedicina.",
            "Enfoque preventivo y seguimiento continuo.",
            "Tratamientos basados en evidencia y educación al paciente.",
            "Más de 10 años acompañando familias en su bienestar.",
        ]

        prof_role = await _get_role_by_code(session, "professional")
        patient_role = await _get_role_by_code(session, "patient")

        demo_professional_ids = []

        for i in range(1, demo_prof_count + 1):
            email = f"prof{i:03d}@demo.com"
            existing_prof = await session.execute(select(User).where(User.email == email))
            existing_user = existing_prof.scalar_one_or_none()
            if existing_user:
                prof_result = await session.execute(
                    select(Professional).where(Professional.user_id == existing_user.id)
                )
                prof = prof_result.scalar_one_or_none()
                if prof:
                    demo_professional_ids.append(prof.id)
                    if specialty_ids:
                        existing_spec = await session.execute(
                            select(ProfessionalSpecialty).where(
                                ProfessionalSpecialty.professional_id == prof.id
                            )
                        )
                        if not existing_spec.scalar_one_or_none():
                            primary_specialty_id = specialty_ids[(i - 1) % len(specialty_ids)]
                            session.add(
                                ProfessionalSpecialty(
                                    professional_id=prof.id,
                                    specialty_id=primary_specialty_id,
                                    is_primary=True,
                                )
                            )
                    for modality in ["in_person_consultorio", "teleconsulta"]:
                        price_amount = Decimal(25 + (i % 40))
                        session.add(
                            ProfessionalPrice(
                                id=str(uuid.uuid4()),
                                professional_id=prof.id,
                                modality_code=modality,
                                amount=price_amount,
                                currency_code="USD",
                                pricing_policy_id="policy_default_15",
                                is_active=True,
                            )
                        )
                continue

            first_name = first_names[(i - 1) % len(first_names)]
            last_name = last_names[(i - 1) % len(last_names)]
            city = cities[(i - 1) % len(cities)]
            province = provinces[(i - 1) % len(provinces)]
            title = titles[(i - 1) % len(titles)]
            bio = bios[(i - 1) % len(bios)]

            user = User(
                email=email,
                password_hash=hash_password("Test1234!"),
                is_email_verified=True,
                status=UserStatus.ACTIVE,
                created_by="seed",
                updated_by="seed",
            )
            session.add(user)
            await session.flush()

            person = Person(
                user_id=user.id,
                first_name=first_name,
                last_name=last_name,
                national_id=f"17000000{i:03d}",
                phone=f"099000{i:03d}",
                country="Ecuador",
                province=province,
                city=city,
                created_by="seed",
                updated_by="seed",
            )
            session.add(person)
            await session.flush()

            professional = Professional(
                user_id=user.id,
                person_id=person.id,
                public_slug=f"prof-{i:03d}",
                professional_type="general",
                public_display_name=f"{first_name} {last_name}",
                bio_public=bio,
                years_experience=str(3 + (i % 15)),
                languages_json='["Español","Inglés"]',
                onboarding_status=OnboardingStatus.APPROVED,
                is_public_profile_enabled=True,
                status=ProfessionalStatus.ACTIVE,
                created_by="seed",
                updated_by="seed",
            )
            session.add(professional)
            await session.flush()

            await session.execute(
                text(
                    "INSERT INTO professional_public_profiles "
                    "(id, professional_id, public_title, public_bio, consultation_price, currency_code, province, city, sector, address_reference, years_experience, languages_json, is_public, searchable_text, created_at, updated_at, deleted_at, version) "
                    "VALUES (:id, :professional_id, :public_title, :public_bio, :consultation_price, :currency_code, :province, :city, :sector, :address_reference, :years_experience, :languages_json, :is_public, :searchable_text, :created_at, :updated_at, :deleted_at, :version)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "professional_id": professional.id,
                    "public_title": title,
                    "public_bio": bio,
                    "consultation_price": Decimal(25 + (i % 40)),
                    "currency_code": "USD",
                    "province": province,
                    "city": city,
                    "sector": "Centro",
                    "address_reference": None,
                    "years_experience": 3 + (i % 15),
                    "languages_json": '["Español","Inglés"]',
                    "is_public": True,
                    "searchable_text": f"{first_name} {last_name} {title} {city}",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "deleted_at": None,
                    "version": "1",
                },
            )

            if specialty_ids:
                primary_specialty_id = specialty_ids[(i - 1) % len(specialty_ids)]
                session.add(
                    ProfessionalSpecialty(
                        professional_id=professional.id,
                        specialty_id=primary_specialty_id,
                        is_primary=True,
                    )
                )

            if prof_role:
                session.add(
                    UserRole(
                        id=f"user_role_prof_{i:03d}",
                        user_id=user.id,
                        role_id=prof_role.id,
                        assigned_by="seed",
                        status=UserRoleStatus.ACTIVE,
                    )
                )

            for weekday in range(7):
                for modality in ["in_person_consultorio", "teleconsulta"]:
                    await session.execute(
                        text(
                            "INSERT INTO professional_availabilities "
                            "(id, professional_id, weekday, start_time, end_time, slot_minutes, modality_code, status, created_at, updated_at, deleted_at, version) "
                            "VALUES (:id, :professional_id, :weekday, :start_time, :end_time, :slot_minutes, :modality_code, :status, :created_at, :updated_at, :deleted_at, :version)"
                        ),
                        {
                            "id": str(uuid.uuid4()),
                            "professional_id": professional.id,
                            "weekday": weekday,
                            "start_time": time(9, 0),
                            "end_time": time(19, 0),
                            "slot_minutes": 30,
                            "modality_code": modality,
                            "status": "active",
                            "created_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow(),
                            "deleted_at": None,
                            "version": "1",
                        },
                    )

            demo_professional_ids.append(professional.id)

            for modality in ["in_person_consultorio", "teleconsulta"]:
                price_amount = Decimal(25 + (i % 40))
                session.add(
                    ProfessionalPrice(
                        id=str(uuid.uuid4()),
                        professional_id=professional.id,
                        modality_code=modality,
                        amount=str(price_amount),
                        currency_code="USD",
                        pricing_policy_id="policy_default_15",
                        is_active=True,
                    )
                )

        demo_patient_email = "patient_demo@example.com"
        existing_patient_user = await session.execute(
            select(User).where(User.email == demo_patient_email)
        )
        patient_user = existing_patient_user.scalar_one_or_none()
        demo_patient = None

        if not patient_user:
            patient_user = User(
                email=demo_patient_email,
                password_hash=hash_password("Test1234!"),
                is_email_verified=True,
                status=UserStatus.ACTIVE,
                created_by="seed",
                updated_by="seed",
            )
            session.add(patient_user)
            await session.flush()

            patient_person = Person(
                user_id=patient_user.id,
                first_name="Paciente",
                last_name="Demo",
                national_id="1710000001",
                phone="0980000001",
                country="Ecuador",
                created_by="seed",
                updated_by="seed",
            )
            session.add(patient_person)
            await session.flush()

            demo_patient = Patient(
                user_id=patient_user.id,
                person_id=patient_person.id,
                status=PatientStatus.ACTIVE,
                created_by="seed",
                updated_by="seed",
            )
            session.add(demo_patient)

            if patient_role:
                session.add(
                    UserRole(
                        id="user_role_patient_demo",
                        user_id=patient_user.id,
                        role_id=patient_role.id,
                        assigned_by="seed",
                        status=UserRoleStatus.ACTIVE,
                    )
                )
        else:
            patient_result = await session.execute(
                select(Patient).where(Patient.user_id == patient_user.id)
            )
            demo_patient = patient_result.scalar_one_or_none()

        if demo_patient:
            if not demo_professional_ids:
                prof_result = await session.execute(
                    select(Professional.id).where(
                        Professional.status == ProfessionalStatus.ACTIVE,
                        Professional.onboarding_status == OnboardingStatus.APPROVED,
                    )
                )
                demo_professional_ids = [row[0] for row in prof_result.all()]

            base_date = datetime.utcnow().date() + timedelta(days=1)
            for i in range(10):
                if not demo_professional_ids:
                    break
                prof_id = demo_professional_ids[i % len(demo_professional_ids)]
                start_dt = datetime.combine(
                    base_date + timedelta(days=i),
                    datetime.min.time(),
                ).replace(hour=10 + (i % 6), minute=0)
                end_dt = start_dt + timedelta(minutes=30)
                public_code = f"APT-DEMO-{i + 1:03d}"

                existing_apt = await session.execute(
                    select(Appointment).where(Appointment.public_code == public_code)
                )
                if existing_apt.scalar_one_or_none():
                    continue

                apt = Appointment(
                    public_code=public_code,
                    patient_id=demo_patient.id,
                    professional_id=prof_id,
                    modality_code="in_person_consultorio",
                    scheduled_start=start_dt,
                    scheduled_end=end_dt,
                    status="confirmed",
                    created_from="seed",
                )
                session.add(apt)
                await session.flush()

                session.add(
                    AppointmentStatusHistory(
                        appointment_id=apt.id,
                        old_status=None,
                        new_status="confirmed",
                        changed_by_user_id=demo_patient.user_id,
                    )
                )

        await session.commit()
        print("Seed completed")


if __name__ == "__main__":
    asyncio.run(seed())
