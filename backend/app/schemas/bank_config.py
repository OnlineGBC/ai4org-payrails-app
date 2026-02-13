from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


class BankConfigCreate(BaseModel):
    bank_name: str
    supported_rails: str  # comma-separated: fednow,rtp,ach,card
    fednow_limit: Decimal = Decimal("500000")
    rtp_limit: Decimal = Decimal("1000000")
    ach_limit: Decimal = Decimal("10000000")
    is_active: bool = True
    oauth_client_id: Optional[str] = None
    oauth_client_secret: Optional[str] = None
    api_base_url: Optional[str] = None


class BankConfigResponse(BaseModel):
    id: str
    bank_name: str
    supported_rails: str
    fednow_limit: Decimal
    rtp_limit: Decimal
    ach_limit: Decimal
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
