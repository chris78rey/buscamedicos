import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Numeric, Text
from app.core.database import Base

class PricingPolicy(Base):
    __tablename__ = "pricing_policies"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    commission_type = Column(String, nullable=False)
    commission_value = Column(Numeric(precision=10, scale=2), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")

class ProfessionalPrice(Base):
    __tablename__ = "professional_prices"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    professional_id = Column(String, nullable=False, index=True)
    modality_code = Column(String, nullable=False)
    amount = Column(Numeric(precision=10, scale=2), nullable=False)
    currency_code = Column(String, default="USD")
    pricing_policy_id = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")

class PaymentIntentStatus:
    CREATED = "created"
    PENDING = "pending"
    AUTHORIZED = "authorized"
    PAID = "paid"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class PaymentStatus:
    PAID = "paid"
    PARTIALLY_REFUNDED = "partially_refunded"
    REFUNDED = "refunded"
    CHARGEBACK = "chargeback"
    VOIDED = "voided"

class PaymentIntent(Base):
    __tablename__ = "payment_intents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    appointment_id = Column(String, nullable=False, index=True)
    patient_id = Column(String, nullable=False, index=True)
    amount_total = Column(String, nullable=False)
    currency_code = Column(String, default="USD")
    status = Column(String, nullable=False)
    provider_code = Column(String, nullable=False)
    provider_reference = Column(String, nullable=True)
    idempotency_key = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_intent_id = Column(String, unique=True, nullable=False)
    appointment_id = Column(String, nullable=False, index=True)
    patient_id = Column(String, nullable=False)
    amount_total = Column(String, nullable=False)
    currency_code = Column(String, nullable=False)
    status = Column(String, nullable=False)
    paid_at = Column(DateTime, nullable=True)
    external_reference = Column(String, nullable=True)
    reconciliation_status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")

class TransactionType:
    INTENT_CREATED = "intent_created"
    PAYMENT_SUCCEEDED = "payment_succeeded"
    PAYMENT_FAILED = "payment_failed"
    REFUND_REQUESTED = "refund_requested"
    REFUND_APPLIED = "refund_applied"
    VOID_APPLIED = "void_applied"

class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_id = Column(String, nullable=True, index=True)
    payment_intent_id = Column(String, nullable=True)
    transaction_type = Column(String, nullable=False)
    amount = Column(Numeric(precision=10, scale=2), nullable=False)
    currency_code = Column(String, nullable=False)
    provider_code = Column(String, nullable=False)
    provider_reference = Column(String, nullable=True)
    raw_response_json = Column(Text, nullable=True)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=True)

class FinancialPaymentStatus:
    UNPAID = "unpaid"
    PENDING = "pending"
    PAID = "paid"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    FAILED = "failed"

class SettlementStatus:
    NOT_READY = "not_ready"
    PENDING_SETTLEMENT = "pending_settlement"
    SETTLED = "settled"
    CANCELLED = "cancelled"

class AppointmentFinancial(Base):
    __tablename__ = "appointment_financials"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    appointment_id = Column(String, unique=True, nullable=False, index=True)
    professional_price_id = Column(String, nullable=False)
    gross_amount = Column(String, nullable=False)
    platform_commission_type = Column(String, nullable=False)
    platform_commission_value = Column(String, nullable=False)
    platform_commission_amount = Column(String, nullable=False)
    professional_net_amount = Column(String, nullable=False)
    currency_code = Column(String, default="USD")
    payment_status = Column(String, nullable=False)
    settlement_status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")

class RefundStatus:
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"

class Refund(Base):
    __tablename__ = "refunds"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_id = Column(String, nullable=False, index=True)
    appointment_id = Column(String, nullable=False, index=True)
    amount = Column(Numeric(precision=10, scale=2), nullable=False)
    currency_code = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    status = Column(String, nullable=False)
    requested_by_user_id = Column(String, nullable=True)
    approved_by_user_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")

class SettlementBatchStatus:
    DRAFT = "draft"
    GENERATED = "generated"
    PAID = "paid"
    CANCELLED = "cancelled"

class SettlementBatch(Base):
    __tablename__ = "settlement_batches"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_code = Column(String, unique=True, nullable=False, index=True)
    professional_id = Column(String, nullable=False, index=True)
    total_gross = Column(String, nullable=False)
    total_commission = Column(String, nullable=False)
    total_net = Column(String, nullable=False)
    currency_code = Column(String, default="USD")
    status = Column(String, nullable=False)
    generated_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(String, default="1")

class SettlementBatchItem(Base):
    __tablename__ = "settlement_batch_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    settlement_batch_id = Column(String, nullable=False, index=True)
    appointment_id = Column(String, nullable=False)
    appointment_financial_id = Column(String, nullable=False)
    gross_amount = Column(String, nullable=False)
    commission_amount = Column(String, nullable=False)
    net_amount = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)