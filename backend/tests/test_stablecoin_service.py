"""Tests for step 3 stablecoin orchestration + multi-asset ledger."""
from decimal import Decimal

import pytest

from app.models.user import User
from app.services.auth_service import hash_password
from app.services.wallet_service import wallet_credit, get_wallet_balance
from app.services import stablecoin_service as sc
from app.services.stablecoin_service import KycRequiredError
from app.services.reconciliation_service import reconcile_wallet


def _make_user(db, user_id="user-sc-1", email="sc1@test.com"):
    u = User(id=user_id, email=email, hashed_password=hash_password("password123"), role="user")
    db.add(u)
    db.commit()
    return u


# --- KYC gating ---

def test_kyc_required_before_crypto_action(db_session):
    _make_user(db_session)
    with pytest.raises(KycRequiredError):
        sc.onramp(db_session, "user-sc-1", Decimal("100"), "USDC")


def test_ensure_kyc_approves_and_unblocks(db_session):
    _make_user(db_session)
    record = sc.ensure_kyc(db_session, "user-sc-1", {"name": "Test"})
    assert record.status == "approved"
    sc.require_kyc_approved(db_session, "user-sc-1")  # no raise


# --- on-ramp / balances ---

def test_onramp_credits_wallet_in_asset(db_session):
    _make_user(db_session)
    sc.ensure_kyc(db_session, "user-sc-1")
    tx = sc.onramp(db_session, "user-sc-1", Decimal("100"), "USDC")

    assert tx.status == "completed"
    assert tx.asset_code == "USDC"
    assert tx.direction == "onramp"
    assert tx.amount is None                 # stablecoin uses base units
    assert tx.amount_base_units == 100_000_000  # 100 * 10^6
    assert get_wallet_balance(db_session, "user-sc-1", "USDC") == Decimal("100")


def test_multi_asset_balances_are_isolated(db_session):
    _make_user(db_session)
    sc.ensure_kyc(db_session, "user-sc-1")
    wallet_credit(db_session, "user-sc-1", Decimal("50"), description="seed usd")  # USD
    sc.onramp(db_session, "user-sc-1", Decimal("100"), "USDC")

    assert get_wallet_balance(db_session, "user-sc-1", "USD") == Decimal("50")
    assert get_wallet_balance(db_session, "user-sc-1", "USDC") == Decimal("100")
    assert get_wallet_balance(db_session, "user-sc-1", "USD1") == Decimal("0")


# --- off-ramp / send ---

def test_offramp_debits_wallet(db_session):
    _make_user(db_session)
    sc.ensure_kyc(db_session, "user-sc-1")
    sc.onramp(db_session, "user-sc-1", Decimal("100"), "USDC")
    sc.offramp(db_session, "user-sc-1", "USDC", Decimal("40"))
    assert get_wallet_balance(db_session, "user-sc-1", "USDC") == Decimal("60")


def test_offramp_insufficient_balance_raises(db_session):
    _make_user(db_session)
    sc.ensure_kyc(db_session, "user-sc-1")
    with pytest.raises(ValueError):
        sc.offramp(db_session, "user-sc-1", "USDC", Decimal("10"))


def test_send_stablecoin_debits_wallet(db_session):
    _make_user(db_session)
    sc.ensure_kyc(db_session, "user-sc-1")
    sc.onramp(db_session, "user-sc-1", Decimal("100"), "USDC")
    tx = sc.send_stablecoin(db_session, "user-sc-1", "0xdead", "USDC", Decimal("25"))
    assert tx.status == "completed"
    assert get_wallet_balance(db_session, "user-sc-1", "USDC") == Decimal("75")


# --- deposit idempotency ---

def test_deposit_is_idempotent_by_tx_hash(db_session):
    _make_user(db_session)
    h = "0xdeposit123"
    sc.credit_deposit(db_session, "user-sc-1", "USDC", Decimal("30"), h)
    sc.credit_deposit(db_session, "user-sc-1", "USDC", Decimal("30"), h)  # replay
    assert get_wallet_balance(db_session, "user-sc-1", "USDC") == Decimal("30")


# --- reconciliation ---

def test_reconcile_wallet_reports_drift(db_session):
    _make_user(db_session)
    sc.ensure_kyc(db_session, "user-sc-1")
    account = sc.ensure_crypto_account(db_session, "user-sc-1", "USDC", "ethereum")
    sc.onramp(db_session, "user-sc-1", Decimal("100"), "USDC")

    report = reconcile_wallet(db_session, "user-sc-1", "USDC", account.partner_account_id)
    # internal ledger shows 100; mock partner account balance is 0 -> drift 100
    assert report["internal_balance"] == Decimal("100")
    assert report["drift"] == Decimal("100")
    assert report["reconciled"] is False
