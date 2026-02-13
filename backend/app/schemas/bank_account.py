from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class BankAccountCreate(BaseModel):
    bank_name: Optional[str] = None
    routing_number: str
    account_number: str
    account_type: str = "checking"


class BankAccountResponse(BaseModel):
    id: str
    merchant_id: str
    bank_name: Optional[str] = None
    routing_number: str
    account_number_last4: Optional[str] = None
    account_type: str
    verification_status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MicroDepositVerify(BaseModel):
    amount_1: str
    amount_2: str
