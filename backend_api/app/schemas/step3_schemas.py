from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PriceUpdate(BaseModel):
    modality_code: str
    amount: float

class PriceResponse(BaseModel):
    id: str
    modality_code: str
    amount: float
    currency_code: str
    is_active: bool

class CheckoutResponse(BaseModel):
    appointment_id: str
    professional_name: str
    modality_code: str
    gross_amount: float
    currency_code: str
    amount_total: float
    payment_status: str

class PaymentIntentCreate(BaseModel):
    idempotency_key: str

class PaymentIntentResponse(BaseModel):
    id: str
    amount_total: float
    status: str
    expires_at: Optional[datetime] = None

class PaymentIntentConfirmResponse(BaseModel):
    payment_id: str
    payment_status: str
    appointment_financial_status: str
    appointment_operational_status: str

class PaymentResponse(BaseModel):
    id: str
    amount_total: float
    currency_code: str
    status: str
    paid_at: Optional[datetime] = None
    external_reference: Optional[str] = None

class RefundRequest(BaseModel):
    reason: str

class RefundResponse(BaseModel):
    id: str
    amount: float
    currency_code: str
    reason: str
    status: str

class SettlementBatchResponse(BaseModel):
    id: str
    batch_code: str
    total_gross: float
    total_commission: float
    total_net: float
    currency_code: str
    status: str
    generated_at: Optional[datetime] = None

class PendingEarningsResponse(BaseModel):
    total_pending_gross: float
    total_pending_commission: float
    total_pending_net: float
    currency_code: str
    appointments_count: int