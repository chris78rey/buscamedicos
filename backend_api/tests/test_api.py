import pytest
import asyncio
from httpx import AsyncClient
from app.main import app
from app.core.database import Base, engine, async_session_maker
from app.core.security import hash_password
from app.models import *

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

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

@pytest.mark.asyncio
async def test_register_patient(client, db_session):
    response = await client.post("/api/v1/auth/register/patient", json={
        "email": "patient@test.com",
        "password": "test123",
        "first_name": "Test",
        "last_name": "Patient",
        "national_id": "1234567890",
        "phone": "0999999999"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

@pytest.mark.asyncio
async def test_register_professional(client, db_session):
    response = await client.post("/api/v1/auth/register/professional", json={
        "email": "prof@test.com",
        "password": "test123",
        "first_name": "Test",
        "last_name": "Professional",
        "national_id": "0987654321",
        "phone": "0999999998"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

@pytest.mark.asyncio
async def test_login_success(client, db_session):
    await client.post("/api/v1/auth/register/patient", json={
        "email": "login@test.com",
        "password": "test123",
        "first_name": "Test",
        "last_name": "User",
        "national_id": "1111111111",
        "phone": "0999999997"
    })
    response = await client.post("/api/v1/auth/login", json={
        "email": "login@test.com",
        "password": "test123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

@pytest.mark.asyncio
async def test_login_invalid_credentials(client, db_session):
    response = await client.post("/api/v1/auth/login", json={
        "email": "nonexistent@test.com",
        "password": "wrong"
    })
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_patient_cannot_access_admin_endpoints(client, db_session):
    reg_response = await client.post("/api/v1/auth/register/patient", json={
        "email": "patient_admin@test.com",
        "password": "test123",
        "first_name": "Test",
        "last_name": "Patient",
        "national_id": "2222222222",
        "phone": "0999999996"
    })
    token = reg_response.json()["access_token"]
    
    response = await client.get("/api/v1/admin/verification-requests", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_agreement_acceptances(client, db_session):
    from app.models.agreement import Agreement, AgreementType, AgreementAcceptance, AcceptanceType
    agreement = Agreement(
        id="test_agreement",
        agreement_type=AgreementType.PLATFORM_TERMS,
        version_code="1.0",
        title="Test Terms",
        content_markdown="Test content",
        is_active=True
    )
    db_session.add(agreement)
    await db_session.commit()
    
    reg_response = await client.post("/api/v1/auth/register/patient", json={
        "email": "agreement@test.com",
        "password": "test123",
        "first_name": "Test",
        "last_name": "User",
        "national_id": "3333333333",
        "phone": "0999999995"
    })
    token = reg_response.json()["access_token"]
    
    response = await client.post(f"/api/v1/agreements/{agreement.id}/accept", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_soft_delete_document(client, db_session):
    reg_response = await client.post("/api/v1/auth/register/professional", json={
        "email": "doc_soft@test.com",
        "password": "test123",
        "first_name": "Test",
        "last_name": "Professional",
        "national_id": "4444444444",
        "phone": "0999999994"
    })
    token = reg_response.json()["access_token"]
    
    from app.models.professional_document import DocumentType
    response = await client.post(
        "/api/v1/professionals/me/documents?document_type=national_id_front",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.txt", b"test content", "text/plain")}
    )

@pytest.mark.asyncio
async def test_audit_event_on_approval(client, db_session):
    from app.models.role import Role, RoleCode
    from app.core.security import hash_password
    from app.models.user import User, UserStatus
    
    admin_user = User(
        id="admin_test",
        email="admin@test.com",
        password_hash=hash_password("admin123"),
        status=UserStatus.ACTIVE
    )
    db_session.add(admin_user)
    
    role_result = await db_session.execute(select(Role).where(Role.code == RoleCode.ADMIN_VALIDATION))
    admin_role = role_result.scalar_one_or_none()
    if not admin_role:
        admin_role = Role(id="role_admin_validation", code=RoleCode.ADMIN_VALIDATION, name="Admin Validation", is_system=True)
        db_session.add(admin_role)
    
    from app.models.role import UserRole
    user_role = UserRole(user_id=admin_user.id, role_id=admin_role.id)
    db_session.add(user_role)
    await db_session.commit()