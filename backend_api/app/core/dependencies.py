from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import User
from app.models.role import Role

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
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
    async def role_checker(current_user: User = Depends(get_current_user)):
        await current_user.awaitable_attrs.roles
        # Check user roles
        has_role = any(role.code in allowed_roles for role in current_user.roles)
        if not has_role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user
    return role_checker

def require_owner_or_role(resource_owner_id: str, allowed_roles: List[str]):
    async def owner_checker(current_user: User = Depends(get_current_user)):
        if str(current_user.id) == resource_owner_id:
            return current_user
        await current_user.awaitable_attrs.roles
        has_role = any(role.code in allowed_roles for role in current_user.roles)
        if not has_role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user
    return owner_checker

def require_non_clinical_admin_scope():
    async def admin_checker(current_user: User = Depends(get_current_user)):
        await current_user.awaitable_attrs.roles
        admin_roles = ["super_admin", "admin_validation", "admin_support"]
        has_admin = any(role.code in admin_roles for role in current_user.roles)
        if has_admin:
            # Admin cannot access clinical data - future enforcement
            pass
        return current_user
    return admin_checker