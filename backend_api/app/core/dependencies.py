from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import User

security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    access_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = None
    if credentials:
        token = credentials.credentials
    elif access_token:
        token = access_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == payload.get("sub")))
    user = result.scalar_one_or_none()
    if not user or user.deleted_at:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

def require_role(allowed_roles: List[str]):
    async def role_checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ):
        from sqlalchemy import select
        from app.models.role import Role, UserRole, UserRoleStatus
        result = await db.execute(
            select(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                UserRole.user_id == current_user.id,
                UserRole.status == UserRoleStatus.ACTIVE
            )
        )
        roles = result.scalars().all()
        has_role = any(role.code in allowed_roles for role in roles)
        if not has_role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user
    return role_checker

def require_owner_or_role(resource_owner_id: str, allowed_roles: List[str]):
    async def owner_checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ):
        if str(current_user.id) == resource_owner_id:
            return current_user
        from sqlalchemy import select
        from app.models.role import Role, UserRole, UserRoleStatus
        result = await db.execute(
            select(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                UserRole.user_id == current_user.id,
                UserRole.status == UserRoleStatus.ACTIVE
            )
        )
        roles = result.scalars().all()
        has_role = any(role.code in allowed_roles for role in roles)
        if not has_role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user
    return owner_checker

def require_non_clinical_admin_scope():
    async def admin_checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ):
        from sqlalchemy import select
        from app.models.role import Role, UserRole, UserRoleStatus
        result = await db.execute(
            select(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                UserRole.user_id == current_user.id,
                UserRole.status == UserRoleStatus.ACTIVE
            )
        )
        roles = result.scalars().all()
        admin_roles = ["super_admin", "admin_validation", "admin_support"]
        has_admin = any(role.code in admin_roles for role in roles)
        if has_admin:
            # Admin cannot access clinical data - future enforcement
            pass
        return current_user
    return admin_checker