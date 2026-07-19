from abc import ABC, abstractmethod
from decimal import Decimal

from app.services.stablecoin.schemas import (
    KycStatus,
    ProviderAccount,
    QuoteResult,
    TransferResult,
)


class StablecoinProviderInterface(ABC):
    """Contract for a regulated stablecoin partner (e.g. Zero Hash).

    Mirrors app/services/bank/interface.py. USDC and USD1 share one
    implementation; the partner owns licensing, KYC/AML, custody, and settlement.
    """

    # --- onboarding / KYC ---
    @abstractmethod
    def submit_kyc(self, user_id: str, payload: dict) -> str:
        """Submit KYC for a user; returns the partner KYC id."""
        ...

    @abstractmethod
    def get_kyc_status(self, partner_kyc_id: str) -> KycStatus:
        ...

    # --- accounts / addresses ---
    @abstractmethod
    def create_account(self, owner_id: str, asset_code: str, network: str) -> ProviderAccount:
        ...

    @abstractmethod
    def get_deposit_address(self, partner_account_id: str, asset_code: str, network: str) -> str:
        ...

    @abstractmethod
    def get_balance(self, partner_account_id: str, asset_code: str) -> Decimal:
        ...

    # --- ramps (USD <-> stablecoin) ---
    @abstractmethod
    def quote_onramp(self, usd_amount: Decimal, asset_code: str) -> QuoteResult:
        ...

    @abstractmethod
    def execute_onramp(self, quote_id: str, idempotency_key: str) -> TransferResult:
        ...

    @abstractmethod
    def quote_offramp(self, asset_amount: Decimal, asset_code: str) -> QuoteResult:
        ...

    @abstractmethod
    def execute_offramp(self, quote_id: str, idempotency_key: str) -> TransferResult:
        ...

    # --- transfers ---
    @abstractmethod
    def transfer(
        self,
        from_account_id: str,
        to_address: str,
        asset_code: str,
        network: str,
        amount: Decimal,
        idempotency_key: str,
    ) -> TransferResult:
        ...

    @abstractmethod
    def get_transfer_status(self, partner_transfer_id: str) -> TransferResult:
        ...

    # --- webhooks ---
    @abstractmethod
    def verify_webhook(self, headers: dict, raw_body: bytes) -> bool:
        ...

    @abstractmethod
    def parse_webhook_event(self, raw_body: bytes) -> dict:
        ...
