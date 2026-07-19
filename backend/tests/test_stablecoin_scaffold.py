"""Smoke tests for the stablecoin scaffolding (steps 1 & 2).

Verifies the new models create/query cleanly and the mock provider satisfies the
StablecoinProviderInterface with basic happy-path behaviour. No business logic is
wired yet, so these only exercise the scaffold surface.
"""
from decimal import Decimal

from app.models.asset import Asset
from app.models.crypto_account import CryptoAccount
from app.models.kyc_record import KycRecord
from app.services.stablecoin import get_stablecoin_provider
from app.services.stablecoin.interface import StablecoinProviderInterface
from app.services.stablecoin.schemas import KycStatus, OnchainStatus


# --- Step 1: data model ---

def test_new_models_persist(db_session):
    db_session.add(Asset(code="USDC", asset_type="stablecoin", decimals=6, display_name="USD Coin"))
    db_session.add(
        CryptoAccount(
            user_id=None, merchant_id=None, partner="zerohash",
            partner_account_id="acct_1", asset_code="USDC", network="ethereum",
            deposit_address="0xabc", status="active",
        )
    )
    db_session.add(KycRecord(user_id="user-x", partner="zerohash", status="approved"))
    db_session.commit()

    assert db_session.query(Asset).filter_by(code="USDC").one().decimals == 6
    assert db_session.query(CryptoAccount).filter_by(partner_account_id="acct_1").one().network == "ethereum"
    assert db_session.query(KycRecord).filter_by(user_id="user-x").one().status == "approved"


def test_transaction_stablecoin_columns_default(db_session):
    from app.models.transaction import Transaction
    tx = Transaction(amount=Decimal("10.00"), idempotency_key="idem-sc-1")
    db_session.add(tx)
    db_session.commit()
    db_session.refresh(tx)
    # Additive columns default to the fiat/offchain values, leaving existing flows unchanged.
    assert tx.asset_code == "USD"
    assert tx.settlement_type == "offchain"


# --- Step 2: provider layer ---

def test_provider_factory_returns_interface():
    provider = get_stablecoin_provider()
    assert isinstance(provider, StablecoinProviderInterface)


def test_mock_provider_happy_path():
    provider = get_stablecoin_provider()

    kyc_id = provider.submit_kyc("user-1", {"name": "Test"})
    assert provider.get_kyc_status(kyc_id) == KycStatus.APPROVED

    account = provider.create_account("user-1", "USDC", "ethereum")
    assert account.deposit_address
    assert provider.get_deposit_address(account.partner_account_id, "USDC", "ethereum") == account.deposit_address

    quote = provider.quote_onramp(Decimal("100"), "USDC")
    result = provider.execute_onramp(quote.quote_id, idempotency_key="onramp-1")
    assert result.status == OnchainStatus.CONFIRMED
    # idempotent
    assert provider.execute_onramp(quote.quote_id, idempotency_key="onramp-1").partner_transfer_id == result.partner_transfer_id

    xfer = provider.transfer(account.partner_account_id, "0xdead", "USDC", "ethereum", Decimal("5"), "send-1")
    assert provider.get_transfer_status(xfer.partner_transfer_id).status == OnchainStatus.CONFIRMED


def test_mock_provider_webhook_helpers():
    provider = get_stablecoin_provider()
    assert provider.verify_webhook({}, b"{}") is True
    assert provider.parse_webhook_event(b'{"event":"deposit"}') == {"event": "deposit"}
