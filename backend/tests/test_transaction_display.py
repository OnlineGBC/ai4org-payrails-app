"""
Tests for sender_name / receiver_name enrichment on PaymentResponse.
Covers:
  - Merchant-to-merchant: both names are merchant names
  - Consumer-to-merchant: sender_name is user email, receiver_name is merchant name
  - All return paths: create, idempotency, get, list, cancel
"""
import uuid
from decimal import Decimal

import pytest

from tests.conftest import get_auth_header, make_auth_header
from app.models.user import User
from app.services.auth_service import hash_password, create_access_token
from app.services.wallet_service import wallet_credit


# ---------------------------------------------------------------------------
# Merchant-to-merchant name enrichment
# ---------------------------------------------------------------------------

class TestMerchantToMerchantNames:
    """POST /payments → both parties are merchants; names come from Merchant.name."""

    def _pay(self, client, sender="merchant-001", receiver="merchant-002", amount="100.00"):
        return client.post("/payments", json={
            "sender_merchant_id": sender,
            "receiver_merchant_id": receiver,
            "amount": amount,
            "idempotency_key": str(uuid.uuid4()),
            "description": "test payment",
        }, headers=get_auth_header())

    def test_create_response_includes_merchant_names(self, client, seed_data):
        resp = self._pay(client)
        assert resp.status_code == 201
        data = resp.json()
        assert data["sender_name"] == "Acme Corp"
        assert data["receiver_name"] == "Globex Inc"

    def test_get_payment_includes_merchant_names(self, client, seed_data):
        create_resp = self._pay(client)
        pid = create_resp.json()["id"]
        resp = client.get(f"/payments/{pid}", headers=get_auth_header())
        assert resp.status_code == 200
        data = resp.json()
        assert data["sender_name"] == "Acme Corp"
        assert data["receiver_name"] == "Globex Inc"

    def test_list_payments_includes_merchant_names(self, client, seed_data):
        self._pay(client)
        resp = client.get(
            "/payments?merchant_id=merchant-001", headers=get_auth_header()
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) >= 1
        for item in items:
            assert item["sender_name"] == "Acme Corp"
            assert item["receiver_name"] == "Globex Inc"

    def test_idempotency_return_includes_names(self, client, seed_data):
        key = str(uuid.uuid4())
        payload = {
            "sender_merchant_id": "merchant-001",
            "receiver_merchant_id": "merchant-002",
            "amount": "50.00",
            "idempotency_key": key,
            "description": "idempotency test",
        }
        headers = get_auth_header()
        resp1 = client.post("/payments", json=payload, headers=headers)
        resp2 = client.post("/payments", json=payload, headers=headers)
        # Both responses must have names — including the idempotency early-return path
        assert resp1.json()["sender_name"] == "Acme Corp"
        assert resp2.json()["sender_name"] == "Acme Corp"
        assert resp1.json()["receiver_name"] == "Globex Inc"
        assert resp2.json()["receiver_name"] == "Globex Inc"
        assert resp1.json()["id"] == resp2.json()["id"]

    def test_cancel_response_includes_names(self, client, seed_data, db_session):
        """If payment is still cancellable, cancel endpoint also enriches names."""
        from app.models.transaction import Transaction

        create_resp = self._pay(client)
        pid = create_resp.json()["id"]

        # Manually force status back to 'processing' so cancel is allowed
        txn = db_session.query(Transaction).filter(Transaction.id == pid).first()
        txn.status = "processing"
        db_session.commit()

        resp = client.post(f"/payments/{pid}/cancel", headers=get_auth_header())
        assert resp.status_code == 200
        data = resp.json()
        assert data["sender_name"] == "Acme Corp"
        assert data["receiver_name"] == "Globex Inc"


# ---------------------------------------------------------------------------
# Consumer-to-merchant name enrichment
# ---------------------------------------------------------------------------

class TestConsumerToMerchantNames:
    """POST /consumer/pay → sender_name is user email; receiver_name is merchant name."""

    @pytest.fixture(autouse=True)
    def consumer_setup(self, db_session, seed_data):
        """Add a consumer user with a seeded wallet to the existing seed_data DB."""
        consumer = User(
            id="user-display-test",
            email="display.consumer@test.com",
            hashed_password=hash_password("password123"),
            role="user",
        )
        db_session.add(consumer)
        db_session.commit()
        wallet_credit(
            db_session, "user-display-test", Decimal("300.00"),
            description="Test seed",
        )

    def _consumer_headers(self):
        token = create_access_token({
            "sub": "user-display-test",
            "email": "display.consumer@test.com",
            "role": "user",
        })
        return {"Authorization": f"Bearer {token}"}

    def test_consumer_pay_sender_name_is_email(self, client):
        resp = client.post("/consumer/pay", json={
            "merchant_id": "merchant-001",
            "amount": "25.00",
            "idempotency_key": str(uuid.uuid4()),
            "description": "lunch",
        }, headers=self._consumer_headers())
        assert resp.status_code == 200
        txn_id = resp.json()["transaction_id"]

        get_resp = client.get(f"/payments/{txn_id}", headers=get_auth_header())
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["sender_name"] == "display.consumer@test.com"
        assert data["receiver_name"] == "Acme Corp"

    def test_consumer_pay_appears_in_list_with_names(self, client):
        client.post("/consumer/pay", json={
            "merchant_id": "merchant-001",
            "amount": "10.00",
            "idempotency_key": str(uuid.uuid4()),
            "description": "coffee",
        }, headers=self._consumer_headers())

        resp = client.get(
            "/payments?user_id=user-display-test", headers=get_auth_header()
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) >= 1
        match = next(
            (i for i in items if i["sender_user_id"] == "user-display-test"), None
        )
        assert match is not None
        assert match["sender_name"] == "display.consumer@test.com"
        assert match["receiver_name"] == "Acme Corp"
