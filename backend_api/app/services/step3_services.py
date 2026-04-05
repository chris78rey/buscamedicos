from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.step3_models import (
    PricingPolicy, ProfessionalPrice, PaymentIntent, Payment, PaymentTransaction,
    AppointmentFinancial, Refund, SettlementBatch, SettlementBatchItem,
    PaymentIntentStatus, PaymentStatus, TransactionType, FinancialPaymentStatus,
    SettlementStatus, RefundStatus, SettlementBatchStatus
)
from app.models.step2_models import Appointment, Professional
from decimal import Decimal

class PaymentProvider:
    async def create_intent(self, amount: float, currency: str, appointment_id: str):
        raise NotImplementedError
    async def confirm_payment(self, intent_id: str):
        raise NotImplementedError
    async def fail_payment(self, intent_id: str):
        raise NotImplementedError
    async def refund_payment(self, payment_id: str, amount: float):
        raise NotImplementedError

class SandboxPaymentProvider(PaymentProvider):
    async def create_intent(self, amount: float, currency: str, appointment_id: str):
        return {
            "provider_reference": f"sandbox_{appointment_id}_{datetime.now().timestamp()}",
            "expires_at": datetime.utcnow() + timedelta(hours=24)
        }
    async def confirm_payment(self, intent_id: str):
        return {"status": "paid", "provider_reference": f"sandbox_confirm_{intent_id}"}
    async def fail_payment(self, intent_id: str):
        return {"status": "failed"}
    async def refund_payment(self, payment_id: str, amount: float):
        return {"status": "refunded", "provider_reference": f"sandbox_refund_{payment_id}"}

class PricingService:
    @staticmethod
    async def get_or_create_financials(db: AsyncSession, appointment_id: str, professional_id: str, modality_code: str):
        existing = await db.execute(
            select(AppointmentFinancial).where(AppointmentFinancial.appointment_id == appointment_id)
        )
        financial = existing.scalar_one_or_none()
        if financial:
            return financial
        
        price_result = await db.execute(
            select(ProfessionalPrice).where(
                and_(
                    ProfessionalPrice.professional_id == professional_id,
                    ProfessionalPrice.modality_code == modality_code,
                    ProfessionalPrice.is_active == True
                )
            )
        )
        price = price_result.scalar_one_or_none()
        if not price:
            raise ValueError("No active price found for this modality")
        
        policy_result = await db.execute(
            select(PricingPolicy).where(PricingPolicy.id == price.pricing_policy_id)
        )
        policy = policy_result.scalar_one_or_none()
        
        gross = Decimal(str(price.amount))
        if policy and policy.commission_type == "percentage":
            commission_pct = Decimal(str(policy.commission_value)) / Decimal("100")
            commission_amount = gross * commission_pct
        else:
            commission_amount = Decimal(policy.commission_value) if policy else Decimal("0")
        
        net = gross - commission_amount
        
        financial = AppointmentFinancial(
            appointment_id=appointment_id,
            professional_price_id=price.id,
            gross_amount=str(gross),
            platform_commission_type=policy.commission_type if policy else "fixed",
            platform_commission_value=str(policy.commission_value) if policy else "0",
            platform_commission_amount=str(commission_amount),
            professional_net_amount=str(net),
            currency_code=price.currency_code or "USD",
            payment_status=FinancialPaymentStatus.UNPAID,
            settlement_status=SettlementStatus.NOT_READY
        )
        db.add(financial)
        await db.flush()
        return financial

class PaymentIntentService:
    @staticmethod
    async def create_intent(db: AsyncSession, appointment_id: str, patient_id: str, idempotency_key: str):
        existing_key = await db.execute(
            select(PaymentIntent).where(PaymentIntent.idempotency_key == idempotency_key)
        )
        existing = existing_key.scalar_one_or_none()
        if existing and existing.status not in [PaymentIntentStatus.FAILED, PaymentIntentStatus.EXPIRED]:
            return existing
        
        apt_result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
        apt = apt_result.scalar_one_or_none()
        if not apt:
            raise ValueError("Appointment not found")
        
        prof_result = await db.execute(select(Professional).where(Professional.id == apt.professional_id))
        prof = prof_result.scalar_one_or_none()
        
        financials = await PricingService.get_or_create_financials(db, appointment_id, apt.professional_id, apt.modality_code)
        
        provider = SandboxPaymentProvider()
        provider_result = await provider.create_intent(float(financials.gross_amount), financials.currency_code, appointment_id)
        
        intent = PaymentIntent(
            appointment_id=appointment_id,
            patient_id=patient_id,
            amount_total=financials.gross_amount,
            currency_code=financials.currency_code,
            status=PaymentIntentStatus.PENDING,
            provider_code="sandbox",
            provider_reference=provider_result.get("provider_reference"),
            idempotency_key=idempotency_key,
            expires_at=provider_result.get("expires_at")
        )
        db.add(intent)
        
        apt.financial_status = FinancialPaymentStatus.PENDING
        financials.payment_status = FinancialPaymentStatus.PENDING
        
        transaction = PaymentTransaction(
            payment_intent_id=intent.id,
            transaction_type=TransactionType.INTENT_CREATED,
            amount=financials.gross_amount,
            currency_code=financials.currency_code,
            provider_code="sandbox",
            status="created"
        )
        db.add(transaction)
        
        await db.commit()
        return intent

class PaymentConfirmationService:
    @staticmethod
    async def confirm_sandbox(db: AsyncSession, intent_id: str, user_id: str):
        intent_result = await db.execute(select(PaymentIntent).where(PaymentIntent.id == intent_id))
        intent = intent_result.scalar_one_or_none()
        if not intent:
            raise ValueError("Payment intent not found")
        if intent.status == PaymentIntentStatus.PAID:
            raise ValueError("Payment already completed")
        
        existing_payment = await db.execute(
            select(Payment).where(Payment.payment_intent_id == intent_id)
        )
        if existing_payment.scalar_one_or_none():
            raise ValueError("Payment record already exists")
        
        provider = SandboxPaymentProvider()
        provider.confirm_payment(intent_id)
        
        payment = Payment(
            payment_intent_id=intent.id,
            appointment_id=intent.appointment_id,
            patient_id=intent.patient_id,
            amount_total=intent.amount_total,
            currency_code=intent.currency_code,
            status=PaymentStatus.PAID,
            paid_at=datetime.utcnow(),
            external_reference=intent.provider_reference
        )
        db.add(payment)
        
        transaction = PaymentTransaction(
            payment_id=payment.id,
            payment_intent_id=intent.id,
            transaction_type=TransactionType.PAYMENT_SUCCEEDED,
            amount=intent.amount_total,
            currency_code=intent.currency_code,
            provider_code="sandbox",
            status="succeeded",
            created_by=user_id
        )
        db.add(transaction)
        
        apt_result = await db.execute(select(Appointment).where(Appointment.id == intent.appointment_id))
        apt = apt_result.scalar_one_or_none()
        if apt:
            apt.financial_status = FinancialPaymentStatus.PAID
        
        fin_result = await db.execute(
            select(AppointmentFinancial).where(AppointmentFinancial.appointment_id == intent.appointment_id)
        )
        fin = fin_result.scalar_one_or_none()
        if fin:
            fin.payment_status = FinancialPaymentStatus.PAID
            fin.settlement_status = SettlementStatus.PENDING_SETTLEMENT
        
        intent.status = PaymentIntentStatus.PAID
        
        await db.commit()
        return {"payment_id": payment.id, "payment_status": payment.status, "appointment_financial_status": fin.payment_status if fin else None}

class RefundService:
    @staticmethod
    async def request_refund(db: AsyncSession, appointment_id: str, user_id: str, reason: str):
        fin_result = await db.execute(
            select(AppointmentFinancial).where(AppointmentFinancial.appointment_id == appointment_id)
        )
        fin = fin_result.scalar_one_or_none()
        if not fin or fin.payment_status != FinancialPaymentStatus.PAID:
            raise ValueError("No paid appointment found")
        
        payment_result = await db.execute(
            select(Payment).where(Payment.appointment_id == appointment_id)
        )
        payment = payment_result.scalar_one_or_none()
        if not payment:
            raise ValueError("No payment found")
        
        refund = Refund(
            payment_id=payment.id,
            appointment_id=appointment_id,
            amount=payment.amount_total,
            currency_code=payment.currency_code,
            reason=reason,
            status=RefundStatus.REQUESTED,
            requested_by_user_id=user_id
        )
        db.add(refund)
        
        fin.payment_status = FinancialPaymentStatus.REFUNDED
        
        await db.commit()
        return refund
    
    @staticmethod
    async def apply_sandbox_refund(db: AsyncSession, refund_id: str, admin_id: str):
        refund_result = await db.execute(select(Refund).where(Refund.id == refund_id))
        refund = refund_result.scalar_one_or_none()
        if not refund:
            raise ValueError("Refund not found")
        
        provider = SandboxPaymentProvider()
        provider.refund_payment(refund.payment_id, float(refund.amount))
        
        refund.status = RefundStatus.APPLIED
        refund.approved_by_user_id = admin_id
        
        fin_result = await db.execute(
            select(AppointmentFinancial).where(AppointmentFinancial.appointment_id == refund.appointment_id)
        )
        fin = fin_result.scalar_one_or_none()
        if fin:
            fin.payment_status = FinancialPaymentStatus.REFUNDED
            fin.settlement_status = SettlementStatus.CANCELLED
        
        await db.commit()
        return refund

class SettlementService:
    @staticmethod
    async def generate_batch(db: AsyncSession, professional_id: str):
        fin_result = await db.execute(
            select(AppointmentFinancial).where(
                and_(
                    AppointmentFinancial.settlement_status == SettlementStatus.PENDING_SETTLEMENT,
                    AppointmentFinancial.deleted_at.is_(None)
                )
            )
        )
        financials = fin_result.scalars().all()
        
        if not financials:
            raise ValueError("No pending settlements found")
        
        total_gross = sum(Decimal(f.gross_amount) for f in financials)
        total_commission = sum(Decimal(f.platform_commission_amount) for f in financials)
        total_net = sum(Decimal(f.professional_net_amount) for f in financials)
        
        batch = SettlementBatch(
            batch_code=f"SB-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            professional_id=professional_id,
            total_gross=str(total_gross),
            total_commission=str(total_commission),
            total_net=str(total_net),
            currency_code="USD",
            status=SettlementBatchStatus.GENERATED,
            generated_at=datetime.utcnow()
        )
        db.add(batch)
        await db.flush()
        
        for fin in financials:
            item = SettlementBatchItem(
                settlement_batch_id=batch.id,
                appointment_id=fin.appointment_id,
                appointment_financial_id=fin.id,
                gross_amount=fin.gross_amount,
                commission_amount=fin.platform_commission_amount,
                net_amount=fin.professional_net_amount
            )
            db.add(item)
            fin.settlement_status = SettlementStatus.SETTLED
        
        await db.commit()
        return batch