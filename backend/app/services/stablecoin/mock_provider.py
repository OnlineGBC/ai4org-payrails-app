"""In-memory mock stablecoin provider (deterministic test/dev double).

Mirrors app/services/bank/mock_bank.py. Behaviour is intentionally simple and
happy-path: KYC auto-approves, ramps settle instantly at ~1:1 with a flat fee,
and transfers return CONFIRMED. No network or randomness.
"""
import json
import uuid
from decimal import Decimal
from typing import Dict

from app.services.stablecoin.interface import StablecoinProviderInterface
from app.services.stablecoin.schemas import (
    KycStatus,
    OnchainStatus,
    ProviderAccount,
    QuoteResult,
    TransferResult,
)

FLAT_FEE = Decimal("0.00")           # mock: no spread
QUOTE_EXPIRES_AT = "2099-01-01T00:00:00Z"


class MockStablecoinProvider(StablecoinProviderInterface):
    def __init__(self) -> None:
        self._kyc: Dict[str, KycStatus] = {}
        self._accounts: Dict[str, ProviderAccount] = {}
        self._balances: Dict[str, Decimal] = {}
        self._quotes: Dict[str, QuoteResult] = {}
        self._transfers: Dict[str, TransferResult] = {}
        self._idempotency: Dict[str, TransferResult] = {}

    # --- onboarding / KYC ---
    def submit_kyc(self, user_id: str, payload: dict) -> str:
        partner_kyc_id = f"kyc_{uuid.uuid4().hex[:12]}"
        self._kyc[partner_kyc_id] = KycStatus.APPROVED  # mock: auto-approve
        return partner_kyc_id

    def get_kyc_status(self, partner_kyc_id: str) -> KycStatus:
        return self._kyc.get(partner_kyc_id, KycStatus.NOT_STARTED)

    # --- accounts / addresses ---
    def create_account(self, owner_id: str, asset_code: str, network: str) -> ProviderAccount:
        partner_account_id = f"acct_{uuid.uuid4().hex[:12]}"
        account = ProviderAccount(
            partner_account_id=partner_account_id,
            asset_code=asset_code,
            network=network,
            deposit_address=f"0x{uuid.uuid4().hex}{uuid.uuid4().hex[:8]}",
        )
        self._accounts[partner_account_id] = account
        self._balances.setdefault(partner_account_id, Decimal("0"))
        return account

    def get_deposit_address(self, partner_account_id: str, asset_code: str, network: str) -> str:
        account = self._accounts.get(partner_account_id)
        return account.deposit_address if account and account.deposit_address else ""

    def get_balance(self, partner_account_id: str, asset_code: str) -> Decimal:
        return self._balances.get(partner_account_id, Decimal("0"))

    # --- ramps ---
    def quote_onramp(self, usd_amount: Decimal, asset_code: str) -> QuoteResult:
        return self._quote("USD", asset_code, usd_amount)

    def quote_offramp(self, asset_amount: Decimal, asset_code: str) -> QuoteResult:
        return self._quote(asset_code, "USD", asset_amount)

    def _quote(self, from_asset: str, to_asset: str, amount: Decimal) -> QuoteResult:
        quote = QuoteResult(
            quote_id=f"quote_{uuid.uuid4().hex[:12]}",
            from_asset=from_asset,
            to_asset=to_asset,
            from_amount=amount,
            to_amount=amount - FLAT_FEE,   # mock: 1:1 minus flat fee
            fee=FLAT_FEE,
            expires_at=QUOTE_EXPIRES_AT,
        )
        self._quotes[quote.quote_id] = quote
        return quote

    def execute_onramp(self, quote_id: str, idempotency_key: str) -> TransferResult:
        return self._settle_quote(quote_id, idempotency_key)

    def execute_offramp(self, quote_id: str, idempotency_key: str) -> TransferResult:
        return self._settle_quote(quote_id, idempotency_key)

    def _settle_quote(self, quote_id: str, idempotency_key: str) -> TransferResult:
        if idempotency_key in self._idempotency:
            return self._idempotency[idempotency_key]
        result = TransferResult(
            partner_transfer_id=f"xfer_{uuid.uuid4().hex[:12]}",
            status=OnchainStatus.CONFIRMED,
            onchain_tx_hash=f"0x{uuid.uuid4().hex}{uuid.uuid4().hex}",
            confirmations=12,
        )
        self._transfers[result.partner_transfer_id] = result
        self._idempotency[idempotency_key] = result
        return result

    # --- transfers ---
    def transfer(
        self,
        from_account_id: str,
        to_address: str,
        asset_code: str,
        network: str,
        amount: Decimal,
        idempotency_key: str,
    ) -> TransferResult:
        if idempotency_key in self._idempotency:
            return self._idempotency[idempotency_key]
        result = TransferResult(
            partner_transfer_id=f"xfer_{uuid.uuid4().hex[:12]}",
            status=OnchainStatus.CONFIRMED,
            onchain_tx_hash=f"0x{uuid.uuid4().hex}{uuid.uuid4().hex}",
            confirmations=12,
        )
        self._transfers[result.partner_transfer_id] = result
        self._idempotency[idempotency_key] = result
        return result

    def get_transfer_status(self, partner_transfer_id: str) -> TransferResult:
        if partner_transfer_id in self._transfers:
            return self._transfers[partner_transfer_id]
        return TransferResult(
            partner_transfer_id=partner_transfer_id,
            status=OnchainStatus.FAILED,
            failure_reason="Transfer not found",
        )

    # --- webhooks ---
    def verify_webhook(self, headers: dict, raw_body: bytes) -> bool:
        return True  # mock: signatures always valid

    def parse_webhook_event(self, raw_body: bytes) -> dict:
        return json.loads(raw_body or b"{}")


# Singleton instance (mirrors mock_bank_service)
mock_stablecoin_provider = MockStablecoinProvider()
