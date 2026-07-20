"""Tests for merchant stablecoin support (balance on the merchant entity) + seeding."""
from decimal import Decimal

from app.models.merchant import Merchant
from app.models.user import User
from app.services.auth_service import hash_password, create_access_token
from app.services.ledger_service import get_balance
from app.services.stablecoin_seed import seed_stablecoin_balances
from app.services.wallet_service import get_wallet_balance


def _merchant(db, uid, mid, email):
    db.add(Merchant(id=mid, name="M", ein="11-1111111", contact_email=email,
                    onboarding_status="active", kyb_status="approved"))
    db.add(User(id=uid, email=email, hashed_password=hash_password("password123"),
                role="merchant_admin", merchant_id=mid))
    db.commit()
    token = create_access_token({"sub": uid, "email": email, "role": "merchant_admin"})
    return {"Authorization": f"Bearer {token}"}


def _usdc(client, headers):
    body = client.get("/stablecoin/balances", headers=headers).json()
    return body, next(Decimal(b["balance"]) for b in body["balances"] if b["asset_code"] == "USDC")


def test_merchant_onramp_credits_merchant_entity(client, db_session):
    headers = _merchant(db_session, "m-u1", "m-1", "m1@test.com")
    client.post("/stablecoin/kyc", json={}, headers=headers)
    assert client.post("/stablecoin/onramp",
                       json={"usd_amount": "500", "asset_code": "USDC"}, headers=headers).status_code == 200

    # Balance is on the merchant entity, not the admin user's wallet.
    assert get_balance(db_session, "m-1", "USDC") == Decimal("500")
    assert get_wallet_balance(db_session, "m-u1", "USDC") == Decimal("0")

    body, usdc = _usdc(client, headers)
    assert body["merchant_id"] == "m-1"
    assert usdc == Decimal("500")


def test_merchant_send_and_offramp(client, db_session):
    headers = _merchant(db_session, "m-u2", "m-2", "m2@test.com")
    client.post("/stablecoin/kyc", json={}, headers=headers)
    client.post("/stablecoin/onramp", json={"usd_amount": "100", "asset_code": "USDC"}, headers=headers)
    assert client.post("/stablecoin/send",
                       json={"to_address": "0xclean", "amount": "30", "asset_code": "USDC"},
                       headers=headers).status_code == 200
    assert client.post("/stablecoin/offramp",
                       json={"amount": "20", "asset_code": "USDC"}, headers=headers).status_code == 200
    assert get_balance(db_session, "m-2", "USDC") == Decimal("50")


def test_merchant_send_blocked_preserves_balance(client, db_session):
    headers = _merchant(db_session, "m-u3", "m-3", "m3@test.com")
    client.post("/stablecoin/kyc", json={}, headers=headers)
    client.post("/stablecoin/onramp", json={"usd_amount": "100", "asset_code": "USDC"}, headers=headers)
    r = client.post("/stablecoin/send",
                    json={"to_address": "0xofac", "amount": "10", "asset_code": "USDC"}, headers=headers)
    assert r.status_code == 403
    assert get_balance(db_session, "m-3", "USDC") == Decimal("100")


def test_seed_stablecoin_balances_idempotent(db_session):
    db_session.add(Merchant(id="biz-1", name="Biz", ein="22-2222222", contact_email="biz1@test.com",
                            onboarding_status="active", kyb_status="approved"))
    db_session.add(User(id="admin-1", email="a1@test.com", hashed_password=hash_password("x"),
                        role="merchant_admin", merchant_id="biz-1"))
    db_session.add(User(id="cons-1", email="c1@test.com", hashed_password=hash_password("x"), role="user"))
    db_session.commit()

    seed_stablecoin_balances(db_session)
    assert get_balance(db_session, "biz-1", "USDC") == Decimal("100000")
    assert get_balance(db_session, "biz-1", "USD1") == Decimal("100000")
    assert get_wallet_balance(db_session, "cons-1", "USDC") == Decimal("1000")
    assert get_wallet_balance(db_session, "cons-1", "USD1") == Decimal("1000")

    # Idempotent: a second run does not double-credit.
    seed_stablecoin_balances(db_session)
    assert get_balance(db_session, "biz-1", "USDC") == Decimal("100000")
    assert get_wallet_balance(db_session, "cons-1", "USDC") == Decimal("1000")
