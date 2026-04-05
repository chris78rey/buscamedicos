from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User


async def require_admin_privacy(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> User:
    await current_user.awaitable_attrs.roles
    role_codes = [r.code for r in current_user.roles]
    if "admin_privacy" not in role_codes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin_privacy role required"
        )
    return current_user


async def require_privacy_auditor(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> User:
    await current_user.awaitable_attrs.roles
    role_codes = [r.code for r in current_user.roles]
    if "privacy_auditor" not in role_codes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="privacy_auditor role required"
        )
    return current_user
