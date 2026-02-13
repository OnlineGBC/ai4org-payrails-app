from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class PaymentCreate(BaseModel):
    sender_merchant_id: str
    receiver_merchant_id: str
    sender_bank_account_id: Optional[str] = None
    receiver_bank_account_id: Optional[str] = None
    amount: Decimal
    currency: str = "USD"
    idempotency_key: str
    preferred_rail: Optional[str] = None  # fednow, rtp, ach, card


class PaymentResponse(BaseModel):
    id: str
    sender_merchant_id: str
    receiver_merchant_id: str
    amount: Decimal
    currency: str
    rail: Optional[str] = None
    status: str
    idempotency_key: str
    reference_id: Optional[str] = None
    failure_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaymentListQuery(BaseModel):
    merchant_id: Optional[str] = None
    status: Optional[str] = None
    rail: Optional[str] = None
    page: int = 1
    page_size: int = 20


class PaymentListResponse(BaseModel):
    items: List[PaymentResponse]
    total: int
    page: int
    page_size: int
