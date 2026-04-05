from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User


def require_moderation_scope(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    async def checker():
        await current_user.awaitable_attrs.roles
        role_codes = [r.code for r in current_user.roles]
        if "admin_moderation" not in role_codes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Moderation access required"
            )
        return current_user
    return checker()


def forbid_clinical_access_for_moderation(current_user: User):
    async def checker():
        await current_user.awaitable_attrs.roles
        role_codes = [r.code for r in current_user.roles]
        if "admin_moderation" in role_codes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Moderators cannot access clinical endpoints"
            )
        return current_user
    return checker()


async def require_admin_moderation(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> User:
    await current_user.awaitable_attrs.roles
    role_codes = [r.code for r in current_user.roles]
    if "admin_moderation" not in role_codes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin_moderation role required"
        )
    return current_user
