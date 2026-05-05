from datetime import datetime
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.models.user import User, UserStatus
from app.models.role import Role, RoleCode, UserRole, UserRoleStatus
from app.models.person import Person
from app.models.patient import Patient
from app.models.professional import Professional, OnboardingStatus, ProfessionalStatus

router = APIRouter()

class RegisterPatientRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    national_id: str
    phone: str

class RegisterProfessionalRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    national_id: str
    phone: str
    professional_type: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str

class AuthMeResponse(BaseModel):
    id: str
    email: str
    is_email_verified: bool
    status: str
    role_codes: List[str]
    primary_role: Optional[str] = None
    actor_type: str

    class Config:
        from_attributes = True

async def assign_role(db: AsyncSession, user_id: str, role_code: str):
    result = await db.execute(select(Role).where(Role.code == role_code))
    role = result.scalar_one_or_none()
    if role:
        user_role = UserRole(user_id=user_id, role_id=role.id)
        db.add(user_role)
        await db.commit()

@router.post("/register/patient", response_model=TokenResponse)
async def register_patient(data: RegisterPatientRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(email=data.email, password_hash=hash_password(data.password), status=UserStatus.ACTIVE)
    db.add(user)
    await db.flush()
    
    person = Person(
        user_id=user.id,
        first_name=data.first_name,
        last_name=data.last_name,
        national_id=data.national_id,
        phone=data.phone
    )
    db.add(person)
    await db.flush()
    
    patient = Patient(user_id=user.id, person_id=person.id)
    db.add(patient)
    
    await assign_role(db, user.id, RoleCode.PATIENT)
    
    await db.commit()
    
    return TokenResponse(
        access_token=create_access_token({"sub": user.id}),
        refresh_token=create_refresh_token({"sub": user.id})
    )

@router.post("/register/professional", response_model=TokenResponse)
async def register_professional(data: RegisterProfessionalRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(email=data.email, password_hash=hash_password(data.password), status=UserStatus.ACTIVE)
    db.add(user)
    await db.flush()
    
    person = Person(
        user_id=user.id,
        first_name=data.first_name,
        last_name=data.last_name,
        national_id=data.national_id,
        phone=data.phone
    )
    db.add(person)
    await db.flush()
    
    professional = Professional(
        user_id=user.id,
        person_id=person.id,
        professional_type=data.professional_type,
        public_display_name=f"{data.first_name} {data.last_name}",
        status=ProfessionalStatus.DRAFT,
        onboarding_status=OnboardingStatus.DRAFT
    )
    db.add(professional)
    
    await assign_role(db, user.id, RoleCode.PROFESSIONAL)
    
    await db.commit()
    
    return TokenResponse(
        access_token=create_access_token({"sub": user.id}),
        refresh_token=create_refresh_token({"sub": user.id})
    )

@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=403, detail="Account not active")
    
    return TokenResponse(
        access_token=create_access_token({"sub": user.id}),
        refresh_token=create_refresh_token({"sub": user.id})
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    from app.core.security import verify_token
    payload = verify_token(data.refresh_token, "refresh")
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    return TokenResponse(
        access_token=create_access_token({"sub": payload["sub"]}),
        refresh_token=create_refresh_token({"sub": payload["sub"]})
    )

@router.get("/me", response_model=AuthMeResponse)
async def auth_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Role.code)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(
            UserRole.user_id == current_user.id,
            UserRole.status == UserRoleStatus.ACTIVE,
        )
    )
    role_codes = sorted([str(row[0]) for row in result.all()])

    primary_role = None
    for candidate in [
        "super_admin",
        "patient",
        "professional",
        "admin_validation",
        "admin_support",
        "admin_moderation",
        "admin_privacy",
        "privacy_auditor",
    ]:
        if candidate in role_codes:
            primary_role = candidate
            break

    actor_type = "unknown"
    if any(code in role_codes for code in ["super_admin", "admin_validation", "admin_support", "admin_moderation", "admin_privacy"]):
        actor_type = "admin"
    elif "professional" in role_codes:
        actor_type = "professional"
    elif "patient" in role_codes:
        actor_type = "patient"

    return AuthMeResponse(
        id=str(current_user.id),
        email=current_user.email,
        is_email_verified=bool(current_user.is_email_verified),
        status=str(current_user.status),
        role_codes=role_codes,
        primary_role=primary_role,
        actor_type=actor_type,
    )