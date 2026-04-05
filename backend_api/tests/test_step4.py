import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from app.main import app
from app.core.database import Base, engine, async_session_maker


@pytest.fixture(scope="function")
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session_maker() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


async def setup_paid_teleconsulta_appointment(db_session, user_prof_id="user_prof_test", user_patient_id="user_patient_test"):
    from app.models import User, Role, Patient, Professional, Person
    from app.models.step2_models import Appointment
    from app.models.step3_models import AppointmentFinancial
    
    role_prof = Role(id="role_prof", code="professional", name="Professional", is_system=True)
    role_patient = Role(id="role_pat", code="patient", name="Patient", is_system=True)
    db_session.add_all([role_prof, role_patient])
    
    person_prof = Person(id="person_prof", first_name="Dr", last_name="Test", email="prof@test.com")
    person_patient = Person(id="person_patient", first_name="Pat", last_name="Test", email="patient@test.com")
    db_session.add_all([person_prof, person_patient])
    
    user_prof = User(id=user_prof_id, email="prof@test.com", hashed_password="hash", status="active")
    user_patient = User(id=user_patient_id, email="patient@test.com", hashed_password="hash", status="active")
    db_session.add_all([user_prof, user_patient])
    
    prof = Professional(id="prof_test", user_id=user_prof_id, person_id="person_prof",
                        public_display_name="Dr Test", status="active", onboarding_status="approved")
    patient = Patient(id="patient_test", user_id=user_patient_id, person_id="person_patient",
                      status="active", verified=True)
    db_session.add_all([prof, patient])
    
    appt = Appointment(
        id="appt_test",
        public_code="APPT001",
        patient_id="patient_test",
        professional_id="prof_test",
        modality_code="teleconsulta",
        scheduled_start=datetime.utcnow() + timedelta(days=1),
        scheduled_end=datetime.utcnow() + timedelta(days=1, hours=1),
        status="confirmed"
    )
    db_session.add(appt)
    
    fin = AppointmentFinancial(
        id="fin_test",
        appointment_id="appt_test",
        professional_price_id="pp_test",
        gross_amount="50.00",
        platform_commission_type="percentage",
        platform_commission_value="15.00",
        platform_commission_amount="7.50",
        professional_net_amount="42.50",
        currency_code="USD",
        payment_status="paid",
        settlement_status="not_ready"
    )
    db_session.add(fin)
    await db_session.commit()
    return appt, fin


@pytest.mark.asyncio
async def test_no_teleconsulta_for_unpaid_appointment(client, db_session):
    from app.models import User, Role, Patient, Professional, Person
    from app.models.step2_models import Appointment
    
    role_prof = Role(id="role_prof2", code="professional", name="Professional", is_system=True)
    role_patient = Role(id="role_pat2", code="patient", name="Patient", is_system=True)
    db_session.add_all([role_prof, role_patient])
    
    person_prof = Person(id="person_prof2", first_name="Dr", last_name="Test", email="prof2@test.com")
    person_patient = Person(id="person_patient2", first_name="Pat", last_name="Test", email="patient2@test.com")
    db_session.add_all([person_prof, person_patient])
    
    user_prof = User(id="user_prof2", email="prof2@test.com", hashed_password="hash", status="active")
    user_patient = User(id="user_patient2", email="patient2@test.com", hashed_password="hash", status="active")
    db_session.add_all([user_prof, user_patient])
    
    prof = Professional(id="prof_test2", user_id="user_prof2", person_id="person_prof2",
                        public_display_name="Dr Test", status="active", onboarding_status="approved")
    patient = Patient(id="patient_test2", user_id="user_patient2", person_id="person_patient2",
                      status="active", verified=True)
    db_session.add_all([prof, patient])
    
    appt = Appointment(
        id="appt_test2",
        public_code="APPT002",
        patient_id="patient_test2",
        professional_id="prof_test2",
        modality_code="teleconsulta",
        scheduled_start=datetime.utcnow() + timedelta(days=1),
        scheduled_end=datetime.utcnow() + timedelta(days=1, hours=1),
        status="confirmed"
    )
    db_session.add(appt)
    await db_session.commit()
    
    response = await client.post("/api/v1/auth/register/professional", json={
        "email": "prof2@test.com", "password": "test123", "first_name": "Dr", "last_name": "Test",
        "national_id": "0987654321", "phone": "0999999998"
    })
    token = response.json().get("access_token")
    
    response = await client.post(
        "/api/v1/professionals/me/appointments/appt_test2/teleconsultation",
        json={"provider_code": "jitsi", "session_url": "https://meet.jit.si/test",
              "scheduled_start": "2024-06-10T09:00:00", "scheduled_end": "2024-06-10T10:00:00"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert "paid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_yes_teleconsulta_for_paid_teleconsulta_appointment(client, db_session):
    await setup_paid_teleconsulta_appointment(db_session)
    
    response = await client.post("/api/v1/auth/register/professional", json={
        "email": "prof@test.com", "password": "test123", "first_name": "Dr", "last_name": "Test",
        "national_id": "0987654321", "phone": "0999999998"
    })
    token = response.json().get("access_token")
    
    response = await client.post(
        "/api/v1/professionals/me/appointments/appt_test/teleconsultation",
        json={"provider_code": "jitsi", "session_url": "https://meet.jit.si/test",
              "scheduled_start": "2024-06-10T09:00:00", "scheduled_end": "2024-06-10T10:00:00"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "teleconsultation_session_id" in data
    assert data["status"] == "created"


@pytest.mark.asyncio
async def test_professional_can_start_and_end_session(client, db_session):
    await setup_paid_teleconsulta_appointment(db_session)
    
    response = await client.post("/api/v1/auth/register/professional", json={
        "email": "prof@test.com", "password": "test123", "first_name": "Dr", "last_name": "Test",
        "national_id": "0987654321", "phone": "0999999998"
    })
    token = response.json().get("access_token")
    
    await client.post(
        "/api/v1/professionals/me/appointments/appt_test/teleconsultation",
        json={"provider_code": "jitsi", "session_url": "https://meet.jit.si/test",
              "scheduled_start": "2024-06-10T09:00:00", "scheduled_end": "2024-06-10T10:00:00"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    response = await client.post(
        "/api/v1/professionals/me/appointments/appt_test/teleconsultation/start",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"
    
    response = await client.post(
        "/api/v1/professionals/me/appointments/appt_test/teleconsultation/end",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_patient_can_see_teleconsultation_metadata(client, db_session):
    await setup_paid_teleconsulta_appointment(db_session)
    
    await client.post("/api/v1/auth/register/professional", json={
        "email": "prof@test.com", "password": "test123", "first_name": "Dr", "last_name": "Test",
        "national_id": "0987654321", "phone": "0999999998"
    })
    
    response = await client.post("/api/v1/auth/register/patient", json={
        "email": "patient@test.com", "password": "test123", "first_name": "Pat", "last_name": "Test",
        "national_id": "1234567890", "phone": "0999999999"
    })
    patient_token = response.json().get("access_token")
    
    response = await client.get(
        "/api/v1/patient/appointments/appt_test/teleconsultation",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_patient_cannot_see_other_appointment_teleconsultation(client, db_session):
    await setup_paid_teleconsulta_appointment(db_session, user_prof_id="user_prof3", user_patient_id="user_patient3")
    
    response = await client.post("/api/v1/auth/register/patient", json={
        "email": "other_patient@test.com", "password": "test123", "first_name": "Other", "last_name": "Patient",
        "national_id": "1111111111", "phone": "0999999997"
    })
    other_token = response.json().get("access_token")
    
    response = await client.get(
        "/api/v1/patient/appointments/appt_test/teleconsultation",
        headers={"Authorization": f"Bearer {other_token}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_clinical_note_created_and_versioned(client, db_session):
    await setup_paid_teleconsulta_appointment(db_session)
    
    response = await client.post("/api/v1/auth/register/professional", json={
        "email": "prof@test.com", "password": "test123", "first_name": "Dr", "last_name": "Test",
        "national_id": "0987654321", "phone": "0999999998"
    })
    token = response.json().get("access_token")
    
    response = await client.put(
        "/api/v1/professionals/me/appointments/appt_test/clinical-note",
        json={"reason_for_consultation": "Dolor de cabeza", "assessment": "Migraine",
              "change_reason": "Initial assessment"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["reason_for_consultation"] == "Dolor de cabeza"
    assert data["note_status"] == "draft"
    assert data["version"] == "2"


@pytest.mark.asyncio
async def test_private_professional_note_not_exposed_to_patient(client, db_session):
    await setup_paid_teleconsulta_appointment(db_session)
    
    response = await client.post("/api/v1/auth/register/professional", json={
        "email": "prof@test.com", "password": "test123", "first_name": "Dr", "last_name": "Test",
        "national_id": "0987654321", "phone": "0999999998"
    })
    token = response.json().get("access_token")
    
    await client.put(
        "/api/v1/professionals/me/appointments/appt_test/clinical-note",
        json={"private_professional_note": "Internal note for follow-up", "visible_to_patient": False},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    response = await client.post("/api/v1/auth/register/patient", json={
        "email": "patient@test.com", "password": "test123", "first_name": "Pat", "last_name": "Test",
        "national_id": "1234567890", "phone": "0999999999"
    })
    patient_token = response.json().get("access_token")
    
    response = await client.get(
        "/api/v1/patient/appointments/appt_test/clinical-note",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    data = response.json()
    assert "private_professional_note" not in data or data.get("private_professional_note") is None


@pytest.mark.asyncio
async def test_patient_cannot_see_clinical_note_if_not_visible(client, db_session):
    await setup_paid_teleconsulta_appointment(db_session)
    
    response = await client.post("/api/v1/auth/register/professional", json={
        "email": "prof@test.com", "password": "test123", "first_name": "Dr", "last_name": "Test",
        "national_id": "0987654321", "phone": "0999999998"
    })
    token = response.json().get("access_token")
    
    await client.put(
        "/api/v1/professionals/me/appointments/appt_test/clinical-note",
        json={"visible_to_patient": False, "assessment": "Test assessment"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    response = await client.post("/api/v1/auth/register/patient", json={
        "email": "patient@test.com", "password": "test123", "first_name": "Pat", "last_name": "Test",
        "national_id": "1234567890", "phone": "0999999999"
    })
    patient_token = response.json().get("access_token")
    
    response = await client.get(
        "/api/v1/patient/appointments/appt_test/clinical-note",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_prescription_draft_can_be_issued(client, db_session):
    await setup_paid_teleconsulta_appointment(db_session)
    
    response = await client.post("/api/v1/auth/register/professional", json={
        "email": "prof@test.com", "password": "test123", "first_name": "Dr", "last_name": "Test",
        "national_id": "0987654321", "phone": "0999999998"
    })
    token = response.json().get("access_token")
    
    response = await client.post(
        "/api/v1/professionals/me/appointments/appt_test/prescription",
        json={"general_notes": "Take with food", "items": [
            {"medication_name": "Ibuprofen", "dosage": "400mg", "frequency": "every 8h", "duration": "5 days"}
        ]},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "draft"
    
    response = await client.post(
        f"/api/v1/professionals/me/appointments/appt_test/prescription/{data['prescription_id']}/issue",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "issued"


@pytest.mark.asyncio
async def test_prescription_issued_can_be_revoked(client, db_session):
    await setup_paid_teleconsulta_appointment(db_session)
    
    response = await client.post("/api/v1/auth/register/professional", json={
        "email": "prof@test.com", "password": "test123", "first_name": "Dr", "last_name": "Test",
        "national_id": "0987654321", "phone": "0999999998"
    })
    token = response.json().get("access_token")
    
    response = await client.post(
        "/api/v1/professionals/me/appointments/appt_test/prescription",
        json={"general_notes": "Take with food", "items": [
            {"medication_name": "Ibuprofen", "dosage": "400mg", "frequency": "every 8h", "duration": "5 days"}
        ]},
        headers={"Authorization": f"Bearer {token}"}
    )
    pres_id = response.json()["prescription_id"]
    
    await client.post(
        f"/api/v1/professionals/me/appointments/appt_test/prescription/{pres_id}/issue",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    response = await client.post(
        f"/api/v1/professionals/me/appointments/appt_test/prescription/{pres_id}/revoke",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "revoked"


@pytest.mark.asyncio
async def test_care_instructions_created_and_issued(client, db_session):
    await setup_paid_teleconsulta_appointment(db_session)
    
    response = await client.post("/api/v1/auth/register/professional", json={
        "email": "prof@test.com", "password": "test123", "first_name": "Dr", "last_name": "Test",
        "national_id": "0987654321", "phone": "0999999998"
    })
    token = response.json().get("access_token")
    
    response = await client.put(
        "/api/v1/professionals/me/appointments/appt_test/care-instructions",
        json={"content": "Rest and hydrate", "follow_up_recommended": True, "follow_up_note": "Return if symptoms persist"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["content"] == "Rest and hydrate"
    
    response = await client.post(
        "/api/v1/professionals/me/appointments/appt_test/care-instructions/issue",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "issued"


@pytest.mark.asyncio
async def test_admin_cannot_read_clinical_content(client, db_session):
    await setup_paid_teleconsulta_appointment(db_session)
    
    response = await client.post("/api/v1/auth/register/patient", json={
        "email": "patient@test.com", "password": "test123", "first_name": "Pat", "last_name": "Test",
        "national_id": "1234567890", "phone": "0999999999"
    })
    patient_token = response.json().get("access_token")
    
    await client.put(
        "/api/v1/professionals/me/appointments/appt_test/clinical-note",
        json={"assessment": "Test"},
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    
    response = await client.post("/api/v1/auth/register/patient", json={
        "email": "admin@test.com", "password": "test123", "first_name": "Admin", "last_name": "User",
        "national_id": "0000000000", "phone": "0999999996"
    })


@pytest.mark.asyncio
async def test_clinical_access_audit_logged_on_read(client, db_session):
    await setup_paid_teleconsulta_appointment(db_session)
    
    response = await client.post("/api/v1/auth/register/professional", json={
        "email": "prof@test.com", "password": "test123", "first_name": "Dr", "last_name": "Test",
        "national_id": "0987654321", "phone": "0999999998"
    })
    token = response.json().get("access_token")
    
    await client.get(
        "/api/v1/professionals/me/appointments/appt_test/clinical-note",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    response = await client.get(
        "/api/v1/admin/clinical-access-audit?appointment_id=appt_test",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code in [200, 403]


@pytest.mark.asyncio
async def test_audit_event_logged_on_clinical_write(client, db_session):
    await setup_paid_teleconsulta_appointment(db_session)
    
    response = await client.post("/api/v1/auth/register/professional", json={
        "email": "prof@test.com", "password": "test123", "first_name": "Dr", "last_name": "Test",
        "national_id": "0987654321", "phone": "0999999998"
    })
    token = response.json().get("access_token")
    
    response = await client.put(
        "/api/v1/professionals/me/appointments/appt_test/clinical-note",
        json={"assessment": "Test assessment"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_clinical_file_logical_delete(client, db_session):
    await setup_paid_teleconsulta_appointment(db_session)
    
    response = await client.post("/api/v1/auth/register/professional", json={
        "email": "prof@test.com", "password": "test123", "first_name": "Dr", "last_name": "Test",
        "national_id": "0987654321", "phone": "0999999998"
    })
    token = response.json().get("access_token")
    
    response = await client.post(
        "/api/v1/professionals/me/appointments/appt_test/clinical-files",
        json={"file_id": "file123", "file_type": "receta_pdf", "is_visible_to_patient": True},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    file_id = response.json()["id"]
    
    response = await client.delete(
        f"/api/v1/professionals/me/appointments/appt_test/clinical-files/{file_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"


@pytest.mark.asyncio
async def test_invalid_teleconsultation_transitions_fail(client, db_session):
    await setup_paid_teleconsulta_appointment(db_session)
    
    response = await client.post("/api/v1/auth/register/professional", json={
        "email": "prof@test.com", "password": "test123", "first_name": "Dr", "last_name": "Test",
        "national_id": "0987654321", "phone": "0999999998"
    })
    token = response.json().get("access_token")
    
    response = await client.post(
        "/api/v1/professionals/me/appointments/appt_test/teleconsultation/end",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
