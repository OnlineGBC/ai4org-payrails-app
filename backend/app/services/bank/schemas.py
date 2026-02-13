from pydantic import BaseModel
from decimal import Decimal
from typing import Optional


class TransferRequest(BaseModel):
    sender_account_id: str
    receiver_account_id: str
    amount: Decimal
    currency: str = "USD"
    rail: str  # fednow, rtp, ach, card
    idempotency_key: str
    memo: Optional[str] = None


class TransferResponse(BaseModel):
    reference_id: str
    status: str  # pending, processing, completed, failed
    rail: str
    amount: Decimal
    failure_reason: Optional[str] = None


class BalanceResponse(BaseModel):
    account_id: str
    available_balance: Decimal
    currency: str = "USD"
