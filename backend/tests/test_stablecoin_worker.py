"""Tests for the stablecoin worker endpoints (step 4): /tasks/settle, /tasks/reconcile."""
from decimal import Decimal

from app.config import settings
from app.models.transaction import Transaction
from app.models.user import User
from app.services import stablecoin_service as sc
from app.services.auth_service import hash_password
from app.services.stablecoin import get_stablecoin_provider
from app.services.units import to_base_units
from app.services.wallet_service import get_wallet_balance

SECRET = "worker-secret"


def _auth(monkeypatch):
    monkeypatch.setattr(settings, "STABLECOIN_WORKER_SECRET", SECRET)
    return {"X-Worker-Secret": SECRET}


def test_settle_requires_secret(client):
    assert client.post("/tasks/settle").status_code == 403


def test_settle_advances_pending(client, db_session, monkeypatch):
    headers = _auth(monkeypatch)
    provider = get_stablecoin_provider()
    ref = provider.transfer("acct", "0xto", "USDC", "ethereum", Decimal("50"), "wk-1").partner_transfer_id

    tx = Transaction(
        receiver_user_id="u-wk", amount=None,
        amount_base_units=to_base_units(Decimal("50"), "USDC"),
        currency="USDC", asset_code="USDC", status="processing",
        idempotency_key="idem-wk-1", settlement_type="onchain",
        settlement_network="ethereum", onchain_status="confirming",
        partner="mock", partner_transfer_id=ref, direction="onramp",
    )
    db_session.add(tx)
    db_session.commit()

    r = client.post("/tasks/settle", headers=headers)
    assert r.status_code == 200
    assert r.json()["settled"] >= 1
    assert get_wallet_balance(db_session, "u-wk", "USDC") == Decimal("50")


def test_reconcile_requires_secret(client):
    assert client.post("/tasks/reconcile").status_code == 403


def test_reconcile_reports_drift(client, db_session, monkeypatch):
    headers = _auth(monkeypatch)
    db_session.add(User(id="u-rec", email="rec@test.com", hashed_password=hash_password("password123"), role="user"))
    db_session.commit()

    sc.ensure_kyc(db_session, "u-rec")
    sc.ensure_crypto_account(db_session, "u-rec", "USDC", "ethereum")
    sc.onramp(db_session, "u-rec", Decimal("100"), "USDC")

    r = client.post("/tasks/reconcile", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["accounts"] >= 1
    assert body["drifted"] >= 1
