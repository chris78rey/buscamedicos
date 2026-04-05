from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.agreement import Agreement, AgreementAcceptance, AcceptanceType, AgreementAcceptanceStatus

router = APIRouter()

class AgreementResponse(BaseModel):
    id: str
    agreement_type: str
    version_code: str
    title: str
    content_markdown: str
    is_active: bool
    
    class Config:
        from_attributes = True

@router.get("/active", response_model=list[AgreementResponse])
async def get_active_agreements(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agreement).where(Agreement.is_active == True))
    return result.scalars().all()

@router.post("/{agreement_id}/accept")
async def accept_agreement(
    agreement_id: str,
    acceptance_type: AcceptanceType = AcceptanceType.CLICKWRAP,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    agreement_result = await db.execute(select(Agreement).where(Agreement.id == agreement_id))
    agreement = agreement_result.scalar_one_or_none()
    if not agreement or not agreement.is_active:
        raise HTTPException(status_code=404, detail="Agreement not found or inactive")
    
    existing = await db.execute(
        select(AgreementAcceptance).where(
            AgreementAcceptance.agreement_id == agreement_id,
            AgreementAcceptance.user_id == current_user.id,
            AgreementAcceptance.status == AgreementAcceptanceStatus.ACCEPTED
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Agreement already accepted")
    
    acceptance = AgreementAcceptance(
        agreement_id=agreement_id,
        user_id=current_user.id,
        acceptance_type=acceptance_type,
        ip_address="0.0.0.0",
        user_agent="API",
        status=AgreementAcceptanceStatus.ACCEPTED
    )
    db.add(acceptance)
    await db.commit()
    
    return {"status": "accepted", "acceptance_id": acceptance.id}