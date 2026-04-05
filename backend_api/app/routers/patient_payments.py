from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.patient import Patient
from app.models.step2_models import Appointment
from app.models.step3_models import PaymentIntent, Payment, AppointmentFinancial
from app.schemas.step3_schemas import (
    PaymentIntentCreate, PaymentIntentResponse, PaymentIntentConfirmResponse,
    CheckoutResponse, PaymentResponse, RefundRequest, RefundResponse
)
from app.services.step3_services import PaymentIntentService, PaymentConfirmationService, RefundService

router = APIRouter()

async def get_patient_from_user(db: AsyncSession, user_id: str):
    result = await db.execute(select(Patient).where(Patient.user_id == user_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@router.get("/appointments/{appointment_id}/checkout")
async def get_checkout(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    patient = await get_patient_from_user(db, current_user.id)
    
    apt_result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    apt = apt_result.scalar_one_or_none()
    if not apt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if apt.patient_id != patient.id:
        raise HTTPException(status_code=403, detail="Not your appointment")
    
    fin_result = await db.execute(
        select(AppointmentFinancial).where(AppointmentFinancial.appointment_id == appointment_id)
    )
    fin = fin_result.scalar_one_or_none()
    
    return CheckoutResponse(
        appointment_id=apt.id,
        professional_name="Professional",
        modality_code=apt.modality_code,
        gross_amount=float(fin.gross_amount) if fin else 0,
        currency_code=fin.currency_code if fin else "USD",
        amount_total=float(fin.gross_amount) if fin else 0,
        payment_status=apt.financial_status if apt else "unpaid"
    )

@router.post("/appointments/{appointment_id}/payment-intent")
async def create_payment_intent(
    appointment_id: str,
    data: PaymentIntentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    patient = await get_patient_from_user(db, current_user.id)
    
    apt_result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    apt = apt_result.scalar_one_or_none()
    if not apt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if apt.patient_id != patient.id:
        raise HTTPException(status_code=403, detail="Not your appointment")
    
    try:
        intent = await PaymentIntentService.create_intent(db, appointment_id, patient.id, data.idempotency_key)
        return PaymentIntentResponse(
            id=intent.id,
            amount_total=float(intent.amount_total),
            status=intent.status,
            expires_at=intent.expires_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/payment-intents/{intent_id}/confirm-sandbox")
async def confirm_sandbox_payment(
    intent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    patient = await get_patient_from_user(db, current_user.id)
    
    intent_result = await db.execute(select(PaymentIntent).where(PaymentIntent.id == intent_id))
    intent = intent_result.scalar_one_or_none()
    if not intent:
        raise HTTPException(status_code=404, detail="Payment intent not found")
    if intent.patient_id != patient.id:
        raise HTTPException(status_code=403, detail="Not your payment")
    
    try:
        result = await PaymentConfirmationService.confirm_sandbox(db, intent_id, current_user.id)
        return PaymentIntentConfirmResponse(
            payment_id=result["payment_id"],
            payment_status=result["payment_status"],
            appointment_financial_status=result["appointment_financial_status"],
            appointment_operational_status=""
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/payment-intents/{intent_id}/fail-sandbox")
async def fail_sandbox_payment(
    intent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    patient = await get_patient_from_user(db, current_user.id)
    
    intent_result = await db.execute(select(PaymentIntent).where(PaymentIntent.id == intent_id))
    intent = intent_result.scalar_one_or_none()
    if not intent:
        raise HTTPException(status_code=404, detail="Payment intent not found")
    
    intent.status = "failed"
    await db.commit()
    return {"status": "failed"}

@router.get("/payments")
async def list_payments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    patient = await get_patient_from_user(db, current_user.id)
    
    result = await db.execute(
        select(Payment).where(Payment.patient_id == patient.id).order_by(Payment.created_at.desc())
    )
    payments = result.scalars().all()
    return [
        PaymentResponse(
            id=p.id,
            amount_total=float(p.amount_total),
            currency_code=p.currency_code,
            status=p.status,
            paid_at=p.paid_at,
            external_reference=p.external_reference
        ) for p in payments
    ]

@router.get("/payments/{payment_id}")
async def get_payment(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    patient = await get_patient_from_user(db, current_user.id)
    
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    p = result.scalar_one_or_none()
    if not p or p.patient_id != patient.id:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return PaymentResponse(
        id=p.id,
        amount_total=float(p.amount_total),
        currency_code=p.currency_code,
        status=p.status,
        paid_at=p.paid_at,
        external_reference=p.external_reference
    )

@router.post("/appointments/{appointment_id}/cancel-with-refund-request")
async def cancel_with_refund(
    appointment_id: str,
    data: RefundRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    patient = await get_patient_from_user(db, current_user.id)
    
    apt_result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    apt = apt_result.scalar_one_or_none()
    if not apt or apt.patient_id != patient.id:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    try:
        refund = await RefundService.request_refund(db, appointment_id, current_user.id, data.reason)
        return RefundResponse(
            id=refund.id,
            amount=float(refund.amount),
            currency_code=refund.currency_code,
            reason=refund.reason,
            status=refund.status
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))