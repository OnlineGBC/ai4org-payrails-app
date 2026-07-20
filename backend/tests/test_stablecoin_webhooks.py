"""Tests for the inbound stablecoin partner webhook (step 4)."""
from decimal import Decimal

from app.models.transaction import Transaction
from app.services.stablecoin import mock_stablecoin_provider
from app.services.units import to_base_units
from app.services.wallet_service import get_wallet_balance


def _deposit_event(eid="evt-1", tx_hash="0xdep1"):
    return {
        "event_id": eid,
        "type": "deposit.confirmed",
        "data": {
            "user_id": "u-wh", "asset_code": "USDC", "amount": "30",
            "onchain_tx_hash": tx_hash, "network": "ethereum",
        },
    }


def test_webhook_deposit_credits_and_is_idempotent(client, db_session):
    r = client.post("/webhooks/stablecoin", json=_deposit_event())
    assert r.status_code == 200
    assert r.json()["status"] == "processed"
    assert get_wallet_balance(db_session, "u-wh", "USDC") == Decimal("30")

    # Redelivery of the same event_id must not double-credit.
    r2 = client.post("/webhooks/stablecoin", json=_deposit_event())
    assert r2.json()["status"] == "already_processed"
    assert get_wallet_balance(db_session, "u-wh", "USDC") == Decimal("30")


def test_webhook_invalid_signature_rejected(client, monkeypatch):
    monkeypatch.setattr(mock_stablecoin_provider, "verify_webhook", lambda headers, raw: False)
    r = client.post("/webhooks/stablecoin", json=_deposit_event(eid="evt-2"))
    assert r.status_code == 401


def test_webhook_missing_event_id_rejected(client):
    r = client.post("/webhooks/stablecoin", json={"type": "deposit.confirmed", "data": {}})
    assert r.status_code == 400


def test_webhook_transfer_updated_settles(client, db_session):
    tx = Transaction(
        receiver_user_id="u-xfer", amount=None,
        amount_base_units=to_base_units(Decimal("40"), "USDC"),
        currency="USDC", asset_code="USDC", status="processing",
        idempotency_key="idem-xfer-wh", settlement_type="onchain",
        settlement_network="ethereum", onchain_status="submitted",
        partner="mock", partner_transfer_id="xfer-wh-1", direction="onramp",
    )
    db_session.add(tx)
    db_session.commit()

    event = {
        "event_id": "evt-x", "type": "transfer.updated",
        "data": {"partner_transfer_id": "xfer-wh-1", "status": "confirmed",
                 "confirmations": 12, "onchain_tx_hash": "0xhh"},
    }
    r = client.post("/webhooks/stablecoin", json=event)
    assert r.status_code == 200

    db_session.refresh(tx)
    assert tx.status == "completed"
    assert get_wallet_balance(db_session, "u-xfer", "USDC") == Decimal("40")
