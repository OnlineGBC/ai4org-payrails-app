"""
Consumer-to-consumer payment tests.

Covers:
  - GET /consumer/users/{user_id} — look up a consumer by user ID
  - POST /consumer/pay with a consumer-merchant as the target
  - Sender wallet debited after a consumer-to-consumer payment
  - Receiver wallet credited after a consumer-to-consumer payment
  - Both directions: consumer1 → consumer2, consumer2 → consumer1
  - Invalid / non-consumer IDs return 404 from the user-lookup endpoint
  - Idempotency on consumer-merchant payments
"""
import uuid
from decimal import Decimal
from unittest.mock import patch, MagicMock

import pytest

from tests.conftest import make_auth_header, CONSUMER_MERCHANTS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _headers(user_id: str, email: str) -> dict:
    return make_auth_header(user_id, email, role="user")


def _wallet_balance(client, user_id: str, email: str) -> float:
    resp = client.get("/consumer/wallet/balance", headers=_headers(user_id, email))
    assert resp.status_code == 200, resp.text
    return float(resp.json()["balance"])


def _consumer_pay(client, user_id: str, email: str, merchant_id: str,
                  amount: str, key: str | None = None,
                  description: str | None = None,
                  expected_status: int = 200) -> dict:
    body = {
        "merchant_id": merchant_id,
        "amount": amount,
        "idempotency_key": key or str(uuid.uuid4()),
    }
    if description is not None:
        body["description"] = description
    resp = client.post("/consumer/pay", json=body, headers=_headers(user_id, email))
    assert resp.status_code == expected_status, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# 1. GET /consumer/users/{user_id} — user lookup endpoint
# ---------------------------------------------------------------------------

class TestConsumerUserLookup:

    def test_lookup_returns_user_info(self, client, consumer_merchant_seed_data):
        """GET /consumer/users/{id} returns id, email, and merchant_id."""
        m_id, _, _, u_id, u_email = CONSUMER_MERCHANTS[0]
        # Any authenticated user can call this endpoint
        resp = client.get(f"/consumer/users/{u_id}",
                          headers=_headers(u_id, u_email))
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["id"] == u_id
        assert data["email"] == u_email
        assert data["merchant_id"] == m_id

    def test_lookup_returns_linked_merchant_id(self, client, consumer_merchant_seed_data):
        """merchant_id in response matches the consumer's linked merchant record."""
        m_id, _, _, u_id, u_email = CONSUMER_MERCHANTS[1]
        resp = client.get(f"/consumer/users/{u_id}",
                          headers=_headers(u_id, u_email))
        assert resp.status_code == 200
        assert resp.json()["merchant_id"] == m_id

    def test_lookup_nonexistent_user_returns_404(self, client, consumer_merchant_seed_data):
        """Looking up a user ID that does not exist returns 404."""
        _, _, _, u_id, u_email = CONSUMER_MERCHANTS[0]
        resp = client.get("/consumer/users/user-does-not-exist",
                          headers=_headers(u_id, u_email))
        assert resp.status_code == 404

    def test_lookup_unauthenticated_returns_401(self, client, consumer_merchant_seed_data):
        """Requests without a token are rejected."""
        _, _, _, u_id, _ = CONSUMER_MERCHANTS[0]
        resp = client.get(f"/consumer/users/{u_id}")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 2. POST /consumer/pay → consumer-merchant target
# ---------------------------------------------------------------------------

class TestConsumerPaysConsumerMerchant:

    def test_consumer1_pays_consumer2_merchant(self, client, consumer_merchant_seed_data):
        """consumer1 can pay consumer2's merchant via POST /consumer/pay."""
        _, _, _, u1_id, u1_email = CONSUMER_MERCHANTS[0]
        m2_id, _, _, _, _ = CONSUMER_MERCHANTS[1]
        with patch("app.services.description_service.generate_description",
                   return_value="Payment between consumers"):
            with patch("app.services.notification_service.notify_transaction"):
                with patch(
                    "app.services.bank.mock_bank.mock_bank_service.initiate_transfer"
                ) as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="completed", reference_id="c2c-ref-1",
                        failure_reason=None,
                    )
                    data = _consumer_pay(client, u1_id, u1_email, m2_id, "50.00")
                    assert data["status"] == "completed"
                    assert "transaction_id" in data

    def test_consumer2_pays_consumer1_merchant(self, client, consumer_merchant_seed_data):
        """consumer2 can pay consumer1's merchant — both directions work."""
        m1_id, _, _, _, _ = CONSUMER_MERCHANTS[0]
        _, _, _, u2_id, u2_email = CONSUMER_MERCHANTS[1]
        with patch("app.services.description_service.generate_description",
                   return_value="Reverse payment"):
            with patch("app.services.notification_service.notify_transaction"):
                with patch(
                    "app.services.bank.mock_bank.mock_bank_service.initiate_transfer"
                ) as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="completed", reference_id="c2c-ref-2",
                        failure_reason=None,
                    )
                    data = _consumer_pay(client, u2_id, u2_email, m1_id, "30.00")
                    assert data["status"] == "completed"

    def test_sender_wallet_debited(self, client, consumer_merchant_seed_data):
        """consumer1's wallet decreases by the settled amount after payment."""
        _, _, _, u1_id, u1_email = CONSUMER_MERCHANTS[0]
        m2_id, _, _, _, _ = CONSUMER_MERCHANTS[1]
        with patch("app.services.description_service.generate_description",
                   return_value="x"):
            with patch("app.services.notification_service.notify_transaction"):
                with patch(
                    "app.services.bank.mock_bank.mock_bank_service.initiate_transfer"
                ) as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="completed", reference_id="c2c-ref-3",
                        failure_reason=None,
                    )
                    before = _wallet_balance(client, u1_id, u1_email)
                    _consumer_pay(client, u1_id, u1_email, m2_id, "80.00",
                                  description="Test debit")
                    after = _wallet_balance(client, u1_id, u1_email)
                    # ACH rail (auto-selected for this amount) — no discount
                    assert after < before
                    assert before - after == pytest.approx(80.00, abs=1.00)

    def test_receiver_wallet_credited(self, client, consumer_merchant_seed_data):
        """consumer2's wallet increases when consumer1 pays consumer2's merchant."""
        _, _, _, u1_id, u1_email = CONSUMER_MERCHANTS[0]
        m2_id, _, _, u2_id, u2_email = CONSUMER_MERCHANTS[1]
        with patch("app.services.description_service.generate_description",
                   return_value="x"):
            with patch("app.services.notification_service.notify_transaction"):
                with patch(
                    "app.services.bank.mock_bank.mock_bank_service.initiate_transfer"
                ) as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="completed", reference_id="c2c-ref-4",
                        failure_reason=None,
                    )
                    before = _wallet_balance(client, u2_id, u2_email)
                    _consumer_pay(client, u1_id, u1_email, m2_id, "60.00",
                                  description="Receiver credit test")
                    after = _wallet_balance(client, u2_id, u2_email)
                    assert after > before
                    assert after - before == pytest.approx(60.00, abs=1.00)

    def test_receiver_wallet_not_credited_on_failed_payment(
        self, client, consumer_merchant_seed_data
    ):
        """consumer2's wallet does NOT change when the bank declines the payment."""
        _, _, _, u1_id, u1_email = CONSUMER_MERCHANTS[0]
        m2_id, _, _, u2_id, u2_email = CONSUMER_MERCHANTS[1]
        with patch("app.services.description_service.generate_description",
                   return_value="x"):
            with patch("app.services.notification_service.notify_transaction"):
                with patch(
                    "app.services.bank.mock_bank.mock_bank_service.initiate_transfer"
                ) as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="failed", reference_id="c2c-ref-5",
                        failure_reason="Declined",
                    )
                    before = _wallet_balance(client, u2_id, u2_email)
                    _consumer_pay(client, u1_id, u1_email, m2_id, "40.00")
                    after = _wallet_balance(client, u2_id, u2_email)
                    assert after == pytest.approx(before)

    def test_fednow_discount_applies_to_consumer_merchant_payment(
        self, client, consumer_merchant_seed_data
    ):
        """FedNow payments to a consumer-merchant settle at amount × 0.9875."""
        _, _, _, u1_id, u1_email = CONSUMER_MERCHANTS[0]
        m2_id, _, _, u2_id, u2_email = CONSUMER_MERCHANTS[1]
        with patch("app.services.description_service.generate_description",
                   return_value="x"):
            with patch("app.services.notification_service.notify_transaction"):
                with patch(
                    "app.services.bank.mock_bank.mock_bank_service.initiate_transfer"
                ) as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="completed", reference_id="c2c-ref-6",
                        failure_reason=None,
                    )
                    before_sender = _wallet_balance(client, u1_id, u1_email)
                    before_receiver = _wallet_balance(client, u2_id, u2_email)

                    body = {
                        "merchant_id": m2_id,
                        "amount": "100.00",
                        "idempotency_key": str(uuid.uuid4()),
                        "preferred_rail": "fednow",
                    }
                    resp = client.post("/consumer/pay", json=body,
                                       headers=_headers(u1_id, u1_email))
                    assert resp.status_code == 200

                    after_sender = _wallet_balance(client, u1_id, u1_email)
                    after_receiver = _wallet_balance(client, u2_id, u2_email)

                    # 100 × 0.9875 = 98.75 settled
                    assert before_sender - after_sender == pytest.approx(98.75, abs=0.01)
                    assert after_receiver - before_receiver == pytest.approx(98.75, abs=0.01)

    def test_insufficient_balance_rejected(self, client, consumer_merchant_seed_data):
        """Payment exceeding sender's wallet balance is rejected with 400."""
        _, _, _, u1_id, u1_email = CONSUMER_MERCHANTS[0]
        m2_id, _, _, _, _ = CONSUMER_MERCHANTS[1]
        _consumer_pay(client, u1_id, u1_email, m2_id, "9999.00",
                      expected_status=400)


# ---------------------------------------------------------------------------
# 3. Idempotency on consumer-merchant payments
# ---------------------------------------------------------------------------

class TestConsumerToConsumerIdempotency:

    def test_same_key_returns_same_transaction(self, client, consumer_merchant_seed_data):
        """Duplicate idempotency key returns the same transaction record."""
        _, _, _, u1_id, u1_email = CONSUMER_MERCHANTS[0]
        m2_id, _, _, _, _ = CONSUMER_MERCHANTS[1]
        key = str(uuid.uuid4())
        r1 = _consumer_pay(client, u1_id, u1_email, m2_id, "10.00", key=key)
        r2 = _consumer_pay(client, u1_id, u1_email, m2_id, "10.00", key=key)
        assert r1["transaction_id"] == r2["transaction_id"]
        assert r1["status"] == r2["status"]

    def test_receiver_credited_exactly_once_on_duplicate_key(
        self, client, consumer_merchant_seed_data
    ):
        """Duplicate submission does not double-credit the receiver's wallet."""
        _, _, _, u1_id, u1_email = CONSUMER_MERCHANTS[0]
        m2_id, _, _, u2_id, u2_email = CONSUMER_MERCHANTS[1]
        key = str(uuid.uuid4())
        with patch("app.services.description_service.generate_description",
                   return_value="x"):
            with patch("app.services.notification_service.notify_transaction"):
                with patch(
                    "app.services.bank.mock_bank.mock_bank_service.initiate_transfer"
                ) as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="completed", reference_id="idem-ref-1",
                        failure_reason=None,
                    )
                    before = _wallet_balance(client, u2_id, u2_email)
                    # Use ACH (no discount) so settled amount == sent amount
                    body = {
                        "merchant_id": m2_id,
                        "amount": "25.00",
                        "idempotency_key": key,
                        "preferred_rail": "ach",
                    }
                    headers = _headers(u1_id, u1_email)
                    client.post("/consumer/pay", json=body, headers=headers)
                    client.post("/consumer/pay", json=body, headers=headers)
                    after = _wallet_balance(client, u2_id, u2_email)
                    # Only one credit should have occurred — exactly $25.00
                    assert after - before == pytest.approx(25.00, abs=0.01)
