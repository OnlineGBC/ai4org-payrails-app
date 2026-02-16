from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


class PaymentRequestCreate(BaseModel):
    amount: Decimal
    currency: str = "USD"
    description: Optional[str] = None
    expires_in_minutes: int = 15


class PaymentRequestResponse(BaseModel):
    id: str
    merchant_id: str
    merchant_name: Optional[str] = None
    amount: Decimal
    currency: str
    description: Optional[str] = None
    status: str
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConsumerPayRequest(BaseModel):
    payment_request_id: str
    idempotency_key: str
    preferred_rail: Optional[str] = None
