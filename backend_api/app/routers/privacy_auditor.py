from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.step7_services import ClinicalAccessLoggingService

router = APIRouter(prefix="", tags=["privacy-auditor"])



async def _require_privacy_auditor(current_user: User = Depends(get_current_user)) -> User:
    from app.models.role import UserRole, UserRoleStatus
    from sqlalchemy import select
    return current_user


@router.get("/access-logs")
async def list_access_logs(
    actor_user_id: Optional[str] = Query(None),
    patient_id: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    limit: int = Query(100, le=1000),
    current_user: User = Depends(_require_privacy_auditor),
    db: AsyncSession = Depends(get_db),
):
    """List clinical access logs - read-only metadata export for privacy auditors."""
    service = ClinicalAccessLoggingService(db)
    logs = await service.export_meta(
        actor_user_id=actor_user_id,
        resource_type=resource_type,
        from_date=from_date,
        to_date=to_date,
    )
    return {"logs": logs, "count": len(logs)}


@router.get("/access-logs/export")
async def export_access_logs(
    actor_user_id: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    current_user: User = Depends(_require_privacy_auditor),
    db: AsyncSession = Depends(get_db),
):
    """Export clinical access logs as JSON - for audit reports."""
    service = ClinicalAccessLoggingService(db)
    logs = await service.export_meta(
        actor_user_id=actor_user_id,
        resource_type=resource_type,
        from_date=from_date,
        to_date=to_date,
    )
    return {
        "exported_at": datetime.utcnow().isoformat(),
        "exported_by": current_user.id,
        "filters": {
            "actor_user_id": actor_user_id,
            "resource_type": resource_type,
            "from_date": from_date.isoformat() if from_date else None,
            "to_date": to_date.isoformat() if to_date else None,
        },
        "logs": logs,
        "total": len(logs),
    }
