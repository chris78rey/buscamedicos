from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.user import User
from app.models.role import RoleCode
from app.models.step3_models import Payment, Refund, SettlementBatch, AppointmentFinancial
from app.services.step3_services import RefundService, SettlementService

router = APIRouter()

@router.get("/payments")
async def list_payments(
    current_user: User = Depends(require_role([RoleCode.ADMIN_VALIDATION, RoleCode.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Payment).order_by(Payment.created_at.desc()).limit(100))
    payments = result.scalars().all()
    return [
        {
            "id": p.id,
            "amount_total": float(p.amount_total),
            "currency_code": p.currency_code,
            "status": p.status,
            "paid_at": p.paid_at,
            "appointment_id": p.appointment_id,
            "patient_id": p.patient_id
        } for p in payments
    ]

@router.get("/payments/{payment_id}")
async def get_payment(
    payment_id: str,
    current_user: User = Depends(require_role([RoleCode.ADMIN_VALIDATION, RoleCode.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {
        "id": p.id,
        "amount_total": float(p.amount_total),
        "currency_code": p.currency_code,
        "status": p.status,
        "paid_at": p.paid_at,
        "appointment_id": p.appointment_id,
        "patient_id": p.patient_id,
        "external_reference": p.external_reference
    }

@router.get("/refunds")
async def list_refunds(
    current_user: User = Depends(require_role([RoleCode.ADMIN_VALIDATION, RoleCode.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Refund).order_by(Refund.created_at.desc()).limit(100))
    refunds = result.scalars().all()
    return [
        {
            "id": r.id,
            "amount": float(r.amount),
            "currency_code": r.currency_code,
            "reason": r.reason,
            "status": r.status,
            "appointment_id": r.appointment_id,
            "requested_by_user_id": r.requested_by_user_id
        } for r in refunds
    ]

@router.post("/refunds/{refund_id}/approve")
async def approve_refund(
    refund_id: str,
    current_user: User = Depends(require_role([RoleCode.ADMIN_VALIDATION, RoleCode.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    refund_result = await db.execute(select(Refund).where(Refund.id == refund_id))
    refund = refund_result.scalar_one_or_none()
    if not refund:
        raise HTTPException(status_code=404, detail="Refund not found")
    
    refund.status = "approved"
    await db.commit()
    return {"status": "approved"}

@router.post("/refunds/{refund_id}/reject")
async def reject_refund(
    refund_id: str,
    current_user: User = Depends(require_role([RoleCode.ADMIN_VALIDATION, RoleCode.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    refund_result = await db.execute(select(Refund).where(Refund.id == refund_id))
    refund = refund_result.scalar_one_or_none()
    if not refund:
        raise HTTPException(status_code=404, detail="Refund not found")
    
    refund.status = "rejected"
    await db.commit()
    return {"status": "rejected"}

@router.post("/refunds/{refund_id}/apply-sandbox")
async def apply_sandbox_refund(
    refund_id: str,
    current_user: User = Depends(require_role([RoleCode.ADMIN_VALIDATION, RoleCode.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    try:
        refund = await RefundService.apply_sandbox_refund(db, refund_id, current_user.id)
        return {"status": refund.status, "id": refund.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/settlements/pending")
async def list_pending_settlements(
    current_user: User = Depends(require_role([RoleCode.ADMIN_VALIDATION, RoleCode.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    from app.models.step3_models import SettlementStatus
    result = await db.execute(
        select(AppointmentFinancial).where(
            AppointmentFinancial.settlement_status == SettlementStatus.PENDING_SETTLEMENT
        )
    )
    financials = result.scalars().all()
    return [
        {
            "id": f.id,
            "appointment_id": f.appointment_id,
            "gross_amount": float(f.gross_amount),
            "net_amount": float(f.professional_net_amount),
            "currency_code": f.currency_code
        } for f in financials
    ]

@router.post("/settlements/generate/{professional_id}")
async def generate_settlement(
    professional_id: str,
    current_user: User = Depends(require_role([RoleCode.ADMIN_VALIDATION, RoleCode.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    try:
        batch = await SettlementService.generate_batch(db, professional_id)
        return {
            "id": batch.id,
            "batch_code": batch.batch_code,
            "status": batch.status
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/settlements/{batch_id}/mark-paid")
async def mark_settlement_paid(
    batch_id: str,
    current_user: User = Depends(require_role([RoleCode.ADMIN_VALIDATION, RoleCode.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(SettlementBatch).where(SettlementBatch.id == batch_id))
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Settlement batch not found")
    
    batch.status = "paid"
    batch.paid_at = datetime.utcnow()
    await db.commit()
    return {"status": "paid", "paid_at": batch.paid_at}