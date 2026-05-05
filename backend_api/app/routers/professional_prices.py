from datetime import datetime
from decimal import Decimal
import uuid
import logging
from typing import List, Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.professional import Professional
from app.models.step3_models import (
    AppointmentFinancial,
    FinancialPaymentStatus,
    PricingPolicy,
    ProfessionalPrice,
    SettlementBatch,
    SettlementStatus,
)
from app.models.user import User
from app.schemas.step3_schemas import (
    PendingEarningsResponse,
    PriceResponse,
    PriceUpdate,
)

router = APIRouter()
logger = logging.getLogger(__name__)


async def get_professional_from_user(db: AsyncSession, user_id: str) -> Professional:
    result = await db.execute(
        select(Professional).where(
            Professional.user_id == str(user_id)
        )
    )
    prof = result.scalar_one_or_none()
    if not prof:
        raise HTTPException(status_code=404, detail="Professional not found")
    return prof


@router.get("/me/prices", response_model=List[PriceResponse])
async def get_my_prices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        prof = await get_professional_from_user(db, str(current_user.id))

        result = await db.execute(
            select(ProfessionalPrice).where(
                and_(
                    ProfessionalPrice.professional_id == str(prof.id),
                    ProfessionalPrice.is_active == True,
                )
            )
        )
        prices = result.scalars().all()

        return [
            PriceResponse(
                id=str(p.id),
                modality_code=p.modality_code,
                amount=float(p.amount),
                currency_code=p.currency_code or "USD",
                is_active=bool(p.is_active),
            )
            for p in prices
        ]
    except Exception as e:
        logger.error(f"Error in get_my_prices: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="No se pudieron cargar los precios")


@router.put("/me/prices")
@router.put("/me/prices/{path_modality_code}")
async def update_my_prices(
    data: PriceUpdate,
    path_modality_code: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        prof = await get_professional_from_user(db, str(current_user.id))
        
        # Priorizar el código del body, si no usar el del path
        target_modality = data.modality_code or path_modality_code
        
        if not target_modality:
            raise HTTPException(status_code=400, detail="Modality code is required")

        # Buscar política por código
        policy_result = await db.execute(
            select(PricingPolicy).where(PricingPolicy.code == "default_percentage_15")
        )

        policy = policy_result.scalar_one_or_none()

        if not policy:
            policy = PricingPolicy(
                id=str(uuid.uuid4()),
                code="default_percentage_15",
                name="Default 15% Commission",
                commission_type="percentage",
                commission_value=Decimal("15.00"),
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(policy)
            await db.flush()

        existing = await db.execute(
            select(ProfessionalPrice).where(
                and_(
                    ProfessionalPrice.professional_id == str(prof.id),
                    ProfessionalPrice.modality_code == target_modality,
                )
            )
        )
        price = existing.scalar_one_or_none()

        if price:
            price.amount = Decimal(str(data.amount))
            price.pricing_policy_id = str(policy.id)
            price.is_active = True
            price.updated_at = datetime.utcnow()
        else:
            price = ProfessionalPrice(
                id=str(uuid.uuid4()),
                professional_id=str(prof.id),
                modality_code=target_modality,
                amount=Decimal(str(data.amount)),
                currency_code="USD",
                pricing_policy_id=str(policy.id),
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(price)
            await db.flush()

        await db.commit()
        await db.refresh(price)

        return PriceResponse(
            id=str(price.id),
            modality_code=price.modality_code,
            amount=float(price.amount),
            currency_code=price.currency_code or "USD",
            is_active=bool(price.is_active),
        )

    except Exception as e:
        logger.error(f"Error in update_my_prices: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail="No se pudo guardar el precio")


@router.get("/me/earnings/pending", response_model=PendingEarningsResponse)
async def get_pending_earnings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    prof = await get_professional_from_user(db, str(current_user.id))

    result = await db.execute(
        select(AppointmentFinancial).where(
            and_(
                AppointmentFinancial.professional_id == str(prof.id),
                AppointmentFinancial.settlement_status == SettlementStatus.PENDING_SETTLEMENT,
                AppointmentFinancial.payment_status == FinancialPaymentStatus.PAID,
            )
        )
    )
    financials = result.scalars().all()

    total_gross = sum(Decimal(str(f.gross_amount)) for f in financials)
    total_commission = sum(Decimal(str(f.platform_commission_amount)) for f in financials)
    total_net = sum(Decimal(str(f.professional_net_amount)) for f in financials)

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
    db: AsyncSession = Depends(get_db),
):
    prof = await get_professional_from_user(db, str(current_user.id))

    result = await db.execute(
        select(SettlementBatch).where(
            SettlementBatch.professional_id == str(prof.id)
        ).order_by(SettlementBatch.created_at.desc())
    )
    batches = result.scalars().all()
    
    return [
        {
            "id": str(b.id),
            "batch_code": b.batch_code,
            "total_gross": float(b.total_gross),
            "total_commission": float(b.total_commission),
            "total_net": float(b.total_net),
            "currency_code": b.currency_code,
            "status": b.status,
            "generated_at": b.generated_at.isoformat() if b.generated_at else None,
            "paid_at": b.paid_at.isoformat() if b.paid_at else None
        } for b in batches
    ]