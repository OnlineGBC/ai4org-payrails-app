"""Zero Hash provider — production implementation (STUB).

Scaffold only: method bodies are intentionally unimplemented. Wiring the Zero
Hash REST API (auth, KYC participant onboarding, accounts, RFQ ramps, withdrawals,
transfer status, webhook signature verification) is tracked as later work.

Config to add when implemented (Secret Manager + app.config):
  ZEROHASH_API_KEY, ZEROHASH_API_SECRET, ZEROHASH_PASSPHRASE,
  ZEROHASH_BASE_URL (sandbox vs production), ZEROHASH_WEBHOOK_SECRET.
"""
from decimal import Decimal

from app.services.stablecoin.interface import StablecoinProviderInterface
from app.services.stablecoin.schemas import (
    KycStatus,
    ProviderAccount,
    QuoteResult,
    TransferResult,
)

_PENDING = "Zero Hash integration pending"


class ZeroHashProvider(StablecoinProviderInterface):
    def __init__(self, api_key: str = "", api_secret: str = "", passphrase: str = "",
                 base_url: str = "", webhook_secret: str = "") -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.base_url = base_url
        self.webhook_secret = webhook_secret

    def submit_kyc(self, user_id: str, payload: dict) -> str:
        raise NotImplementedError(_PENDING)

    def get_kyc_status(self, partner_kyc_id: str) -> KycStatus:
        raise NotImplementedError(_PENDING)

    def create_account(self, owner_id: str, asset_code: str, network: str) -> ProviderAccount:
        raise NotImplementedError(_PENDING)

    def get_deposit_address(self, partner_account_id: str, asset_code: str, network: str) -> str:
        raise NotImplementedError(_PENDING)

    def get_balance(self, partner_account_id: str, asset_code: str) -> Decimal:
        raise NotImplementedError(_PENDING)

    def quote_onramp(self, usd_amount: Decimal, asset_code: str) -> QuoteResult:
        raise NotImplementedError(_PENDING)

    def execute_onramp(self, quote_id: str, idempotency_key: str) -> TransferResult:
        raise NotImplementedError(_PENDING)

    def quote_offramp(self, asset_amount: Decimal, asset_code: str) -> QuoteResult:
        raise NotImplementedError(_PENDING)

    def execute_offramp(self, quote_id: str, idempotency_key: str) -> TransferResult:
        raise NotImplementedError(_PENDING)

    def transfer(self, from_account_id: str, to_address: str, asset_code: str,
                 network: str, amount: Decimal, idempotency_key: str) -> TransferResult:
        raise NotImplementedError(_PENDING)

    def get_transfer_status(self, partner_transfer_id: str) -> TransferResult:
        raise NotImplementedError(_PENDING)

    def verify_webhook(self, headers: dict, raw_body: bytes) -> bool:
        raise NotImplementedError(_PENDING)

    def parse_webhook_event(self, raw_body: bytes) -> dict:
        raise NotImplementedError(_PENDING)
