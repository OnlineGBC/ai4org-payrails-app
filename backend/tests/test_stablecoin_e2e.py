"""Step 8: end-to-end integration tests for the stablecoin feature.

These drive the full stack over HTTP (the client fixture) to verify steps 3-7
work together: API -> orchestration -> multi-asset ledger, webhooks -> settlement,
worker -> reconciliation, screening, and idempotency.
"""
from decimal import Decimal

from app.config import settings
from app.models.user import User
from app.services.auth_service import hash_password, create_access_token


def _consumer(db, uid, email=None):
    email = email or f"{uid}@test.com"
    db.add(User(id=uid, email=email, hashed_password=hash_password("password123"), role="user"))
    db.commit()
    token = create_access_token({"sub": uid, "email": email, "role": "user"})
    return {"Authorization": f"Bearer {token}"}


def _bal(client, headers, asset):
    body = client.get("/stablecoin/balances", headers=headers).json()
    return next(Decimal(b["balance"]) for b in body["balances"] if b["asset_code"] == asset)


def test_full_consumer_journey(client, db_session):
    h = _consumer(db_session, "e2e-1")

    assert client.post("/stablecoin/kyc", json={}, headers=h).json()["status"] == "approved"
    assert client.post("/stablecoin/onramp",
                       json={"usd_amount": "200", "asset_code": "USDC"}, headers=h).status_code == 200
    assert _bal(client, h, "USDC") == Decimal("200")

    account = client.post("/stablecoin/accounts",
                          json={"asset_code": "USDC", "network": "ethereum"}, headers=h).json()
    assert account["deposit_address"]

    assert client.post("/stablecoin/send",
                       json={"to_address": "0xclean", "amount": "50", "asset_code": "USDC"},
                       headers=h).status_code == 200
    assert client.post("/stablecoin/offramp",
                       json={"amount": "30", "asset_code": "USDC"}, headers=h).status_code == 200

    assert _bal(client, h, "USDC") == Decimal("120")  # 200 - 50 - 30

    rows = client.get("/stablecoin/transactions?asset_code=USDC", headers=h).json()
    directions = {r["direction"] for r in rows}
    assert {"onramp", "send", "offramp"}.issubset(directions)


def test_deposit_via_webhook_reflected_in_api_balance(client, db_session):
    h = _consumer(db_session, "e2e-2")
    event = {
        "event_id": "e2e-dep-1", "type": "deposit.confirmed",
        "data": {"user_id": "e2e-2", "asset_code": "USDC", "amount": "75",
                 "onchain_tx_hash": "0xe2edep", "network": "ethereum"},
    }
    assert client.post("/webhooks/stablecoin", json=event).status_code == 200
    assert _bal(client, h, "USDC") == Decimal("75")


def test_webhook_deposit_idempotent_end_to_end(client, db_session):
    h = _consumer(db_session, "e2e-3")
    event = {
        "event_id": "e2e-dep-2", "type": "deposit.confirmed",
        "data": {"user_id": "e2e-3", "asset_code": "USDC", "amount": "40",
                 "onchain_tx_hash": "0xe2edep2", "network": "ethereum"},
    }
    client.post("/webhooks/stablecoin", json=event)
    client.post("/webhooks/stablecoin", json=event)  # redelivery
    assert _bal(client, h, "USDC") == Decimal("40")


def test_cross_asset_isolation_via_api(client, db_session):
    h = _consumer(db_session, "e2e-4")
    client.post("/stablecoin/kyc", json={}, headers=h)
    client.post("/stablecoin/onramp", json={"usd_amount": "100", "asset_code": "USDC"}, headers=h)
    client.post("/stablecoin/onramp", json={"usd_amount": "40", "asset_code": "USD1"}, headers=h)

    assert _bal(client, h, "USDC") == Decimal("100")
    assert _bal(client, h, "USD1") == Decimal("40")


def test_send_blocked_via_api_preserves_balance(client, db_session):
    h = _consumer(db_session, "e2e-5")
    client.post("/stablecoin/kyc", json={}, headers=h)
    client.post("/stablecoin/onramp", json={"usd_amount": "100", "asset_code": "USDC"}, headers=h)

    r = client.post("/stablecoin/send",
                    json={"to_address": "0xofacwallet", "amount": "10", "asset_code": "USDC"},
                    headers=h)
    assert r.status_code == 403
    assert _bal(client, h, "USDC") == Decimal("100")  # untouched


def test_reconcile_via_worker_after_api_activity(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "STABLECOIN_WORKER_SECRET", "e2e-wsec")
    h = _consumer(db_session, "e2e-6")
    client.post("/stablecoin/kyc", json={}, headers=h)
    client.post("/stablecoin/accounts", json={"asset_code": "USDC", "network": "ethereum"}, headers=h)
    client.post("/stablecoin/onramp", json={"usd_amount": "100", "asset_code": "USDC"}, headers=h)

    r = client.post("/tasks/reconcile", headers={"X-Worker-Secret": "e2e-wsec"})
    assert r.status_code == 200
    # internal ledger shows 100, mock partner balance 0 -> drift reported
    assert r.json()["drifted"] >= 1
