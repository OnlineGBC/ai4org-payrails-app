"""Tests for step 7 security hardening: webhook HMAC + API rate limiting."""
import hashlib
import hmac
import json

from app.config import settings
from app.models.user import User
from app.services.auth_service import hash_password, create_access_token


def _consumer_headers(db, uid="sec-u", email="secu@test.com"):
    db.add(User(id=uid, email=email, hashed_password=hash_password("password123"), role="user"))
    db.commit()
    token = create_access_token({"sub": uid, "email": email, "role": "user"})
    return {"Authorization": f"Bearer {token}"}


# --- webhook HMAC verification ---

def _signed_body(secret):
    body = json.dumps({
        "event_id": "sec-evt-1", "type": "deposit.confirmed",
        "data": {"user_id": "sec-dep", "asset_code": "USDC", "amount": "5",
                 "onchain_tx_hash": "0xsec1", "network": "ethereum"},
    }).encode()
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return body, sig


def test_webhook_valid_hmac_accepted(client, monkeypatch):
    monkeypatch.setattr(settings, "STABLECOIN_WEBHOOK_SECRET", "whsecret")
    body, sig = _signed_body("whsecret")
    r = client.post("/webhooks/stablecoin", content=body,
                    headers={"Content-Type": "application/json", "X-Signature": sig})
    assert r.status_code == 200


def test_webhook_bad_hmac_rejected(client, monkeypatch):
    monkeypatch.setattr(settings, "STABLECOIN_WEBHOOK_SECRET", "whsecret")
    body, _ = _signed_body("whsecret")
    r = client.post("/webhooks/stablecoin", content=body,
                    headers={"Content-Type": "application/json", "X-Signature": "deadbeef"})
    assert r.status_code == 401


def test_webhook_missing_signature_rejected(client, monkeypatch):
    monkeypatch.setattr(settings, "STABLECOIN_WEBHOOK_SECRET", "whsecret")
    body, _ = _signed_body("whsecret")
    r = client.post("/webhooks/stablecoin", content=body,
                    headers={"Content-Type": "application/json"})
    assert r.status_code == 401


# --- API rate limiting ---

def test_rate_limit_returns_429_over_threshold(client, db_session, monkeypatch):
    headers = _consumer_headers(db_session)
    monkeypatch.setattr(settings, "RATE_LIMIT_MAX_REQUESTS", 3)
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)

    for _ in range(3):
        assert client.get("/stablecoin/balances", headers=headers).status_code == 200
    assert client.get("/stablecoin/balances", headers=headers).status_code == 429


def test_rate_limit_disabled_allows_all(client, db_session, monkeypatch):
    headers = _consumer_headers(db_session)
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", False)
    for _ in range(6):
        assert client.get("/stablecoin/balances", headers=headers).status_code == 200
