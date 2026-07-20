from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class OnchainStatus(str, Enum):
    SUBMITTED = "submitted"
    CONFIRMING = "confirming"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    REORGED = "reorged"


class KycStatus(str, Enum):
    NOT_STARTED = "not_started"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ProviderAccount(BaseModel):
    """A custodial account/address as returned by the partner (not the DB row)."""
    partner_account_id: str
    asset_code: str
    network: str
    deposit_address: Optional[str] = None


class TransferResult(BaseModel):
    partner_transfer_id: str
    status: OnchainStatus
    onchain_tx_hash: Optional[str] = None
    confirmations: int = 0
    failure_reason: Optional[str] = None


class QuoteResult(BaseModel):
    quote_id: str
    from_asset: str
    to_asset: str
    from_amount: Decimal
    to_amount: Decimal
    fee: Decimal
    expires_at: str
