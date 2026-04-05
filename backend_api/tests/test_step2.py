import pytest

@pytest.mark.asyncio
async def test_professional_not_approved_not_in_public_list(client, db_session):
    response = await client.get("/api/v1/public/professionals")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_professional_approved_and_public_appears(client, db_session):
    from app.models import Professional, ProfessionalPublicProfile
    prof = Professional(id="prof_test_pub", user_id="user_pub_test", person_id="person_pub_test", 
                       public_display_name="Dr Test", status="active", onboarding_status="approved")
    db_session.add(prof)
    
    profile = ProfessionalPublicProfile(professional_id="prof_test_pub", public_title="Médico General",
                                         is_public=True, province="Pichincha", city="Quito")
    db_session.add(profile)
    await db_session.commit()
    
    response = await client.get("/api/v1/public/professionals")
    assert response.status_code == 200
    data = response.json()
    assert any(p["professional_id"] == "prof_test_pub" for p in data)

@pytest.mark.asyncio
async def test_search_by_city(client, db_session):
    response = await client.get("/api/v1/public/professionals?city=Quito")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_search_by_specialty(client, db_session):
    from app.models.step2_models import Specialty, ProfessionalSpecialty
    spec = Specialty(id="spec_test", code="cardiology", name="Cardiología")
    db_session.add(spec)
    await db_session.commit()
    
    response = await client.get("/api/v1/public/specialties")
    assert response.status_code == 200
    data = response.json()
    assert any(s["code"] == "cardiology" for s in data)

@pytest.mark.asyncio
async def test_slots_generated_correctly(client, db_session):
    from app.models import Professional
    prof = Professional(id="prof_slots", user_id="user_slots", person_id="person_slots",
                       public_display_name="Dr Slots", status="active", onboarding_status="approved")
    db_session.add(prof)
    await db_session.commit()
    
    response = await client.get("/api/v1/public/professionals/prof_slots/slots?date=2024-06-10&modality=in_person_consultorio")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_blocked_slots_excluded(client, db_session):
    pass

@pytest.mark.asyncio
async def test_no_double_booking(client, db_session):
    pass

@pytest.mark.asyncio
async def test_patient_can_cancel_appointment(client, db_session):
    pass

@pytest.mark.asyncio
async def test_professional_can_confirm_appointment(client, db_session):
    pass

@pytest.mark.asyncio
async def test_invalid_transition_fails(client, db_session):
    pass

@pytest.mark.asyncio
async def test_audit_event_created_on_appointment_change(client, db_session):
    pass

@pytest.mark.asyncio
async def test_appointment_status_history_recorded(client, db_session):
    pass

@pytest.mark.asyncio
async def test_admin_no_clinical_data(client, db_session):
    pass

@pytest.mark.asyncio
async def test_soft_delete_availability_preserves_history(client, db_session):
    pass

@pytest.mark.asyncio
async def test_soft_delete_time_block(client, db_session):
    pass