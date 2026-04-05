from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.step7_models import ExceptionalAccessRequest, ExceptionalAccessRequestStatus

router = APIRouter()

class AccessExceptionRequest(BaseModel):
    target_user_id: str
    resource_type: str
    resource_id: str
    reason: str

@router.post("/access-exception-requests")
async def create_access_exception_request(
    data: AccessExceptionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    request = ExceptionalAccessRequest(
        requester_user_id=current_user.id,
        target_user_id=data.target_user_id,
        resource_type=data.resource_type,
        resource_id=data.resource_id,
        reason=data.reason,
        status=ExceptionalAccessRequestStatus.REQUESTED
    )
    db.add(request)
    await db.commit()
    return {"id": request.id, "status": "requested"}

@router.get("/access-exception-requests/my-requests")
async def get_my_requests(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    result = await db.execute(select(ExceptionalAccessRequest).where(ExceptionalAccessRequest.requester_user_id == current_user.id))
    return result.scalars().all()