"""Tests for step 5 compliance hooks: KYT screening, audit trail, event logging."""
from decimal import Decimal

import pytest

from app.models.event_log import EventLog
from app.models.sanctions_screening import SanctionsScreening
from app.models.user import User
from app.services import stablecoin_service as sc
from app.services.auth_service import hash_password
from app.services.reporting_service import onchain_audit_trail, ctr_report, screening_report
from app.services.screening_service import ScreeningBlockedError
from app.services.wallet_service import get_wallet_balance


def _user(db, uid="u-cmp", email="cmp@test.com"):
    db.add(User(id=uid, email=email, hashed_password=hash_password("password123"), role="user"))
    db.commit()


def _funded(db, uid="u-cmp", amount="100"):
    _user(db, uid)
    sc.ensure_kyc(db, uid)
    sc.onramp(db, uid, Decimal(amount), "USDC")


# --- KYT screening gate ---

def test_send_to_blocked_address_is_rejected_without_debit(db_session):
    _funded(db_session)
    with pytest.raises(ScreeningBlockedError):
        sc.send_stablecoin(db_session, "u-cmp", "0xBADactor", "USDC", Decimal("10"))

    # Funds untouched and the block is recorded for audit.
    assert get_wallet_balance(db_session, "u-cmp", "USDC") == Decimal("100")
    blocked = db_session.query(SanctionsScreening).filter(SanctionsScreening.result == "block").all()
    assert len(blocked) == 1
    assert db_session.query(EventLog).filter(EventLog.event_type == "stablecoin.screening_block").count() == 1


def test_send_to_clean_address_passes_screening(db_session):
    _funded(db_session)
    tx = sc.send_stablecoin(db_session, "u-cmp", "0xclean", "USDC", Decimal("10"))
    assert tx.status == "completed"
    assert get_wallet_balance(db_session, "u-cmp", "USDC") == Decimal("90")

    row = db_session.query(SanctionsScreening).filter(SanctionsScreening.transaction_id == tx.id).one()
    assert row.result == "pass"


# --- on-chain audit trail ---

def test_audit_trail_links_onchain_identifiers(db_session):
    _funded(db_session)
    trail = onchain_audit_trail(db_session, asset_code="USDC")
    assert len(trail) >= 1
    row = trail[0]
    assert row["onchain_tx_hash"]
    assert row["direction"] == "onramp"
    assert row["asset_code"] == "USDC"


def test_ctr_report_flags_large_transactions(db_session):
    _user(db_session)
    sc.ensure_kyc(db_session, "u-cmp")
    sc.onramp(db_session, "u-cmp", Decimal("15000"), "USDC")   # over threshold
    sc.onramp(db_session, "u-cmp", Decimal("100"), "USDC")     # under threshold

    report = ctr_report(db_session)
    amounts = {r["amount"] for r in report}
    assert Decimal("15000") in amounts
    assert Decimal("100") not in amounts


# --- event logging ---

def test_stablecoin_events_logged(db_session):
    _funded(db_session)
    types = {e.event_type for e in db_session.query(EventLog).all()}
    assert "stablecoin.kyc_approved" in types
    assert "stablecoin.onramp" in types


def test_screening_report_excludes_pass_by_default(db_session):
    _funded(db_session)
    sc.send_stablecoin(db_session, "u-cmp", "0xclean", "USDC", Decimal("5"))  # pass row
    with pytest.raises(ScreeningBlockedError):
        sc.send_stablecoin(db_session, "u-cmp", "0xofac", "USDC", Decimal("5"))  # block row

    default_report = screening_report(db_session)
    assert all(r["result"] != "pass" for r in default_report)
    assert any(r["result"] == "block" for r in default_report)
    assert len(screening_report(db_session, include_pass=True)) >= 2
