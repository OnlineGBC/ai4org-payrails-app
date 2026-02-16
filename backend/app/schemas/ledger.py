from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


class LedgerEntry(BaseModel):
    id: str
    merchant_id: str
    transaction_id: Optional[str] = None
    entry_type: str
    amount: Decimal
    balance_after: Decimal
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BalanceResponse(BaseModel):
    merchant_id: str
    balance: Decimal


class WalletBalanceResponse(BaseModel):
    user_id: str
    balance: Decimal
