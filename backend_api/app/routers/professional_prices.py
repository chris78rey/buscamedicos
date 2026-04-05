from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.professional import Professional
from app.models.step3_models import ProfessionalPrice, PricingPolicy, AppointmentFinancial, SettlementBatch
from app.schemas.step3_schemas import PriceUpdate, PriceResponse, PendingEarningsResponse

router = APIRouter()

async def get_professional_from_user(db: AsyncSession, user_id: str):
    result = await db.execute(select(Professional).where(Professional.user_id == user_id))
    prof = result.scalar_one_or_none()
    if not prof:
        raise HTTPException(status_code=404, detail="Professional not found")
    return prof

@router.get("/me/prices")
async def get_my_prices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    prof = await get_professional_from_user(db, current_user.id)
    
    result = await db.execute(
        select(ProfessionalPrice).where(
            and_(
                ProfessionalPrice.professional_id == prof.id,
                ProfessionalPrice.is_active == True
            )
        )
    )
    prices = result.scalars().all()
    return [PriceResponse(
        id=p.id,
        modality_code=p.modality_code,
        amount=float(p.amount),
        currency_code=p.currency_code,
        is_active=p.is_active
    ) for p in prices]

@router.put("/me/prices")
async def update_my_prices(
    data: PriceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    prof = await get_professional_from_user(db, current_user.id)
    
    policy_result = await db.execute(
        select(PricingPolicy).where(PricingPolicy.code == "default_percentage_15", PricingPolicy.is_active == True)
    )
    policy = policy_result.scalar_one_or_none()
    if not policy:
        policy = PricingPolicy(
            id="policy_default",
            code="default_percentage_15",
            name="Default 15% Commission",
            commission_type="percentage",
            commission_value="15.00",
            is_active=True
        )
        db.add(policy)
        await db.flush()
    
    existing = await db.execute(
        select(ProfessionalPrice).where(
            and_(
                ProfessionalPrice.professional_id == prof.id,
                ProfessionalPrice.modality_code == data.modality_code
            )
        )
    )
    price = existing.scalar_one_or_none()
    
    if price:
        price.amount = str(data.amount)
        price.pricing_policy_id = policy.id
        price.updated_at = datetime.utcnow()
    else:
        price = ProfessionalPrice(
            professional_id=prof.id,
            modality_code=data.modality_code,
            amount=str(data.amount),
            currency_code="USD",
            pricing_policy_id=policy.id,
            is_active=True
        )
        db.add(price)
    
    await db.commit()
    return PriceResponse(
        id=price.id,
        modality_code=price.modality_code,
        amount=float(price.amount),
        currency_code=price.currency_code,
        is_active=price.is_active
    )

@router.get("/me/earnings/pending")
async def get_pending_earnings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    prof = await get_professional_from_user(db, current_user.id)
    
    from app.models.step3_models import SettlementStatus, FinancialPaymentStatus
    result = await db.execute(
        select(AppointmentFinancial).where(
            and_(
                AppointmentFinancial.settlement_status == SettlementStatus.PENDING_SETTLEMENT,
                AppointmentFinancial.deleted_at.is_(None)
            )
        )
    )
    financials = result.scalars().all()
    
    from decimal import Decimal
    total_gross = sum(Decimal(f.gross_amount) for f in financials)
    total_commission = sum(Decimal(f.platform_commission_amount) for f in financials)
    total_net = sum(Decimal(f.professional_net_amount) for f in financials)
    
    return PendingEarningsResponse(
        total_pending_gross=float(total_gross),
        total_pending_commission=float(total_commission),
        total_pending_net=float(total_net),
        currency_code="USD",
        appointments_count=len(financials)
    )

@router.get("/me/earnings/settlements")
async def get_my_settlements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    prof = await get_professional_from_user(db, current_user.id)
    
    result = await db.execute(
        select(SettlementBatch).where(
            SettlementBatch.professional_id == prof.id
        ).order_by(SettlementBatch.created_at.desc())
    )
    batches = result.scalars().all()
    return [
        {
            "id": b.id,
            "batch_code": b.batch_code,
            "total_gross": float(b.total_gross),
            "total_commission": float(b.total_commission),
            "total_net": float(b.total_net),
            "currency_code": b.currency_code,
            "status": b.status,
            "generated_at": b.generated_at,
            "paid_at": b.paid_at
        } for b in batches
    ]