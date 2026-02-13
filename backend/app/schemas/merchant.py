from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MerchantCreate(BaseModel):
    name: str
    ein: Optional[str] = None
    contact_email: str
    contact_phone: Optional[str] = None
    sponsor_bank_id: Optional[str] = None


class MerchantUpdate(BaseModel):
    name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    sponsor_bank_id: Optional[str] = None


class MerchantResponse(BaseModel):
    id: str
    name: str
    ein: Optional[str] = None
    contact_email: str
    contact_phone: Optional[str] = None
    onboarding_status: str
    kyb_status: str
    sponsor_bank_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class KYBSubmit(BaseModel):
    ein: str
    business_name: str
    business_address: Optional[str] = None
    representative_name: Optional[str] = None
    representative_ssn_last4: Optional[str] = None
