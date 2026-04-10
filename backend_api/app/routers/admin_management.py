from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
import uuid

from app.core.database import get_db
from app.core.dependencies import require_role
from app.core.security import hash_password
from app.models.user import User, UserStatus
from app.models.role import Role, UserRole, UserRoleStatus, RoleCode

router = APIRouter(prefix="/admin/management", tags=["admin-management"])

# --- SCHEMAS ---
class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    role_code: RoleCode

class AdminUserResponse(BaseModel):
    id: str
    email: str
    status: str
    roles: List[str]

# --- ENDPOINTS ---

@router.get("/users", response_model=List[AdminUserResponse])
async def list_admin_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["super_admin"]))
):
    """Lista todos los usuarios que tienen al menos un rol administrativo."""
    stmt = (
        select(User)
        .join(UserRole, UserRole.user_id == User.id)
        .join(Role, Role.id == UserRole.role_id)
        .where(Role.code.in_([
            RoleCode.SUPER_ADMIN, 
            RoleCode.ADMIN_VALIDATION, 
            RoleCode.ADMIN_SUPPORT
        ]))
        .distinct()
    )
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    response = []
    for user in users:
        role_stmt = select(Role.code).join(UserRole).where(UserRole.user_id == user.id)
        role_result = await db.execute(role_stmt)
        response.append(AdminUserResponse(
            id=str(user.id),
            email=user.email,
            status=user.status,
            roles=[str(r[0]) for r in role_result.all()]
        ))
    return response

@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_admin_user(
    data: AdminUserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["super_admin"]))
):
    """Crea un nuevo usuario y le asigna un rol administrativo."""
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = User(
        id=str(uuid.uuid4()),
        email=data.email,
        password_hash=hash_password(data.password),
        status=UserStatus.ACTIVE,
        is_email_verified=True
    )
    db.add(new_user)
    
    role_result = await db.execute(select(Role).where(Role.code == data.role_code.value))
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role code not found")

    user_role = UserRole(
        user_id=new_user.id,
        role_id=role.id,
        assigned_by=str(current_user.id),
        status=UserRoleStatus.ACTIVE
    )
    db.add(user_role)
    
    await db.commit()
    return {"message": "Admin user created successfully", "id": new_user.id}

@router.get("/roles")
async def list_available_admin_roles(
    current_user: User = Depends(require_role(["super_admin"]))
):
    """Lista los códigos de roles disponibles para staff."""
    return [
        {"code": RoleCode.ADMIN_VALIDATION, "name": "Validador Médico"},
        {"code": RoleCode.ADMIN_SUPPORT, "name": "Soporte Técnico"},
        {"code": RoleCode.SUPER_ADMIN, "name": "Super Administrador"},
    ]
