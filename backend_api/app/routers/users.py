from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.role import Role, UserRole, UserRoleStatus

router = APIRouter()


class UserMeResponse(BaseModel):
    id: str
    email: str
    is_email_verified: bool
    status: str
    role_codes: List[str]
    primary_role: Optional[str] = None
    actor_type: str

    class Config:
        from_attributes = True


@router.get("/me", response_model=UserMeResponse)
async def get_me(
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
    ]:
        if candidate in role_codes:
            primary_role = candidate
            break

    actor_type = "unknown"
    if any(code in role_codes for code in ["super_admin", "admin_validation", "admin_support"]):
        actor_type = "admin"
    elif "patient" in role_codes:
        actor_type = "patient"
    elif "professional" in role_codes:
        actor_type = "professional"

    return UserMeResponse(
        id=str(current_user.id),
        email=current_user.email,
        is_email_verified=bool(current_user.is_email_verified),
        status=str(current_user.status),
        role_codes=role_codes,
        primary_role=primary_role,
        actor_type=actor_type,
    )


@router.patch("/me")
async def update_me(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    for key, value in data.items():
        if hasattr(current_user, key) and key not in ["id", "email", "password_hash"]:
            setattr(current_user, key, value)

    await db.commit()
    await db.refresh(current_user)
    return current_user