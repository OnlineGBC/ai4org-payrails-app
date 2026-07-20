"""Tests for the user-facing stablecoin API (step 6 backend)."""
from decimal import Decimal

from app.models.user import User
from app.services.auth_service import hash_password, create_access_token


def _headers(uid, email, role="user"):
    token = create_access_token({"sub": uid, "email": email, "role": role})
    return {"Authorization": f"Bearer {token}"}


def _consumer(db, uid="api-u", email="apiu@test.com"):
    db.add(User(id=uid, email=email, hashed_password=hash_password("password123"), role="user"))
    db.commit()
    return _headers(uid, email, "user")


def _usdc_balance(client, headers):
    body = client.get("/stablecoin/balances", headers=headers).json()
    return next(Decimal(b["balance"]) for b in body["balances"] if b["asset_code"] == "USDC")


# --- auth / role ---

def test_requires_auth(client):
    assert client.get("/stablecoin/balances").status_code in (401, 403)


def test_rejects_merchant_role(client, db_session):
    db_session.add(User(id="api-m", email="apim@test.com", hashed_password=hash_password("x"), role="merchant_admin"))
    db_session.commit()
    headers = _headers("api-m", "apim@test.com", "merchant_admin")
    assert client.get("/stablecoin/balances", headers=headers).status_code == 403


# --- KYC ---

def test_kyc_submit_and_status(client, db_session):
    headers = _consumer(db_session)
    assert client.get("/stablecoin/kyc", headers=headers).json()["status"] == "not_started"
    r = client.post("/stablecoin/kyc", json={"first_name": "A", "last_name": "B"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["status"] == "approved"
    assert client.get("/stablecoin/kyc", headers=headers).json()["status"] == "approved"


def test_onramp_requires_kyc(client, db_session):
    headers = _consumer(db_session)
    r = client.post("/stablecoin/onramp", json={"usd_amount": "100", "asset_code": "USDC"}, headers=headers)
    assert r.status_code == 403  # KYC not approved


# --- accounts ---

def test_create_and_list_accounts(client, db_session):
    headers = _consumer(db_session)
    r = client.post("/stablecoin/accounts", json={"asset_code": "USDC", "network": "ethereum"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["deposit_address"]
    assert len(client.get("/stablecoin/accounts", headers=headers).json()) == 1


# --- ramps / send / balances ---

def test_onramp_credits_balance(client, db_session):
    headers = _consumer(db_session)
    client.post("/stablecoin/kyc", json={}, headers=headers)
    r = client.post("/stablecoin/onramp", json={"usd_amount": "100", "asset_code": "USDC"}, headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["direction"] == "onramp"
    assert body["status"] == "completed"
    assert _usdc_balance(client, headers) == Decimal("100")


def test_send_then_offramp_reduce_balance(client, db_session):
    headers = _consumer(db_session)
    client.post("/stablecoin/kyc", json={}, headers=headers)
    client.post("/stablecoin/onramp", json={"usd_amount": "100", "asset_code": "USDC"}, headers=headers)

    assert client.post("/stablecoin/send", json={"to_address": "0xclean", "amount": "10", "asset_code": "USDC"}, headers=headers).status_code == 200
    assert client.post("/stablecoin/offramp", json={"amount": "20", "asset_code": "USDC"}, headers=headers).status_code == 200
    assert _usdc_balance(client, headers) == Decimal("70")


def test_send_to_blocked_address_forbidden(client, db_session):
    headers = _consumer(db_session)
    client.post("/stablecoin/kyc", json={}, headers=headers)
    client.post("/stablecoin/onramp", json={"usd_amount": "100", "asset_code": "USDC"}, headers=headers)
    r = client.post("/stablecoin/send", json={"to_address": "0xbadwallet", "amount": "10", "asset_code": "USDC"}, headers=headers)
    assert r.status_code == 403
    assert _usdc_balance(client, headers) == Decimal("100")  # not debited


def test_unsupported_asset_rejected(client, db_session):
    headers = _consumer(db_session)
    client.post("/stablecoin/kyc", json={}, headers=headers)
    r = client.post("/stablecoin/onramp", json={"usd_amount": "100", "asset_code": "USD"}, headers=headers)
    assert r.status_code == 400


def test_transactions_history_filtered(client, db_session):
    headers = _consumer(db_session)
    client.post("/stablecoin/kyc", json={}, headers=headers)
    client.post("/stablecoin/onramp", json={"usd_amount": "50", "asset_code": "USDC"}, headers=headers)
    rows = client.get("/stablecoin/transactions?asset_code=USDC", headers=headers).json()
    assert len(rows) >= 1
    assert all(r["asset_code"] == "USDC" for r in rows)
