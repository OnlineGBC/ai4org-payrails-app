"""
Wallet transfer tests (POST /wallet/send).

Covers:
  - Consumer → consumer wallet transfer
  - Merchant → consumer wallet transfer
  - Sender balance debited, receiver balance credited
  - Insufficient balance returns 400
  - Invalid receiver returns 400
  - Merchant role cannot be a receiver
  - Idempotency
  - AI description generated
  - Notification sent to receiver
  - Transfer visible in receiver's transaction listing
"""
import uuid
from decimal import Decimal
from unittest.mock import patch, MagicMock

import pytest

from tests.conftest import make_auth_header, MULTI_CONSUMERS, MULTI_MERCHANTS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _consumer_headers(user_id: str, email: str) -> dict:
    return make_auth_header(user_id, email, role="user")


def _merchant_headers(user_id: str, email: str) -> dict:
    return make_auth_header(user_id, email, role="merchant_admin")


def _wallet_send(client, headers: dict, receiver_user_id: str,
                 amount: str, key: str | None = None,
                 description: str | None = None,
                 expected_status: int = 200) -> dict:
    body = {
        "receiver_user_id": receiver_user_id,
        "amount": amount,
        "idempotency_key": key or str(uuid.uuid4()),
    }
    if description is not None:
        body["description"] = description
    resp = client.post("/wallet/send", json=body, headers=headers)
    assert resp.status_code == expected_status, resp.text
    return resp.json()


def _consumer_balance(client, user_id: str, email: str) -> float:
    headers = _consumer_headers(user_id, email)
    resp = client.get("/consumer/wallet/balance", headers=headers)
    assert resp.status_code == 200
    return float(resp.json()["balance"])


def _merchant_balance(client, merchant_id: str, user_id: str, email: str) -> float:
    headers = _merchant_headers(user_id, email)
    resp = client.get(f"/payments/balance?merchant_id={merchant_id}", headers=headers)
    assert resp.status_code == 200
    return float(resp.json()["balance"])


# ---------------------------------------------------------------------------
# 1. Consumer → consumer transfers
# ---------------------------------------------------------------------------

class TestConsumerToConsumerTransfer:

    def test_basic_consumer_to_consumer(self, client, full_seed_data):
        """consumer1 can send money to consumer2."""
        u1_id, u1_email = MULTI_CONSUMERS[0]
        u2_id, _ = MULTI_CONSUMERS[1]
        headers = _consumer_headers(u1_id, u1_email)
        data = _wallet_send(client, headers, u2_id, "50.00")
        assert data["status"] == "completed"
        assert "transaction_id" in data

    def test_sender_wallet_debited(self, client, full_seed_data):
        """Sender's wallet decreases by the transfer amount."""
        u1_id, u1_email = MULTI_CONSUMERS[0]
        u2_id, _ = MULTI_CONSUMERS[1]
        with patch("app.services.description_service.generate_description",
                   return_value="x"):
            with patch("app.services.notification_service.notify_transaction"):
                before = _consumer_balance(client, u1_id, u1_email)
                headers = _consumer_headers(u1_id, u1_email)
                _wallet_send(client, headers, u2_id, "75.00")
                after = _consumer_balance(client, u1_id, u1_email)
                assert after == pytest.approx(before - 75.00)

    def test_receiver_wallet_credited(self, client, full_seed_data):
        """Receiver's wallet increases by the transfer amount."""
        u1_id, u1_email = MULTI_CONSUMERS[0]
        u2_id, u2_email = MULTI_CONSUMERS[1]
        with patch("app.services.description_service.generate_description",
                   return_value="x"):
            with patch("app.services.notification_service.notify_transaction"):
                before = _consumer_balance(client, u2_id, u2_email)
                headers = _consumer_headers(u1_id, u1_email)
                _wallet_send(client, headers, u2_id, "30.00")
                after = _consumer_balance(client, u2_id, u2_email)
                assert after == pytest.approx(before + 30.00)

    def test_no_rail_discount_on_wallet_transfer(self, client, full_seed_data):
        """Wallet transfers settle at face value — no FedNow/RTP discount."""
        u1_id, u1_email = MULTI_CONSUMERS[0]
        u2_id, u2_email = MULTI_CONSUMERS[1]
        with patch("app.services.description_service.generate_description",
                   return_value="x"):
            with patch("app.services.notification_service.notify_transaction"):
                before = _consumer_balance(client, u2_id, u2_email)
                headers = _consumer_headers(u1_id, u1_email)
                _wallet_send(client, headers, u2_id, "100.00")
                after = _consumer_balance(client, u2_id, u2_email)
                # Exactly 100 credited — no discount
                assert after == pytest.approx(before + 100.00)


# ---------------------------------------------------------------------------
# 2. Merchant → consumer transfers
# ---------------------------------------------------------------------------

class TestMerchantToConsumerTransfer:

    def test_merchant_can_send_to_consumer(self, client, full_seed_data):
        """A merchant admin can send money to a consumer wallet."""
        m_id, _, _, m_email, m_user_id = MULTI_MERCHANTS[0]
        u_id, _ = MULTI_CONSUMERS[0]
        headers = _merchant_headers(m_user_id, m_email)
        data = _wallet_send(client, headers, u_id, "25.00")
        assert data["status"] == "completed"

    def test_merchant_balance_debited(self, client, full_seed_data):
        """Merchant ledger is debited after sending to a consumer."""
        m_id, _, _, m_email, m_user_id = MULTI_MERCHANTS[0]
        u_id, _ = MULTI_CONSUMERS[0]
        with patch("app.services.description_service.generate_description",
                   return_value="x"):
            with patch("app.services.notification_service.notify_transaction"):
                before = _merchant_balance(client, m_id, m_user_id, m_email)
                headers = _merchant_headers(m_user_id, m_email)
                _wallet_send(client, headers, u_id, "200.00")
                after = _merchant_balance(client, m_id, m_user_id, m_email)
                assert after == pytest.approx(before - 200.00)

    def test_consumer_balance_credited_from_merchant(self, client, full_seed_data):
        """Consumer wallet is credited when a merchant sends to it."""
        m_id, _, _, m_email, m_user_id = MULTI_MERCHANTS[0]
        u_id, u_email = MULTI_CONSUMERS[1]
        with patch("app.services.description_service.generate_description",
                   return_value="x"):
            with patch("app.services.notification_service.notify_transaction"):
                before = _consumer_balance(client, u_id, u_email)
                headers = _merchant_headers(m_user_id, m_email)
                _wallet_send(client, headers, u_id, "150.00")
                after = _consumer_balance(client, u_id, u_email)
                assert after == pytest.approx(before + 150.00)


# ---------------------------------------------------------------------------
# 3. Error cases
# ---------------------------------------------------------------------------

class TestWalletTransferErrors:

    def test_insufficient_consumer_balance_returns_400(self, client, full_seed_data):
        """Consumer cannot send more than their wallet balance."""
        u1_id, u1_email = MULTI_CONSUMERS[0]
        u2_id, _ = MULTI_CONSUMERS[1]
        headers = _consumer_headers(u1_id, u1_email)
        _wallet_send(client, headers, u2_id, "99999.00", expected_status=400)

    def test_insufficient_merchant_balance_returns_400(self, client, full_seed_data):
        """Merchant cannot send more than their ledger balance."""
        m_id, _, _, m_email, m_user_id = MULTI_MERCHANTS[0]
        u_id, _ = MULTI_CONSUMERS[0]
        headers = _merchant_headers(m_user_id, m_email)
        _wallet_send(client, headers, u_id, "999999.00", expected_status=400)

    def test_nonexistent_receiver_returns_400(self, client, full_seed_data):
        """Sending to a user ID that doesn't exist returns 400."""
        u1_id, u1_email = MULTI_CONSUMERS[0]
        headers = _consumer_headers(u1_id, u1_email)
        _wallet_send(client, headers, "user-does-not-exist", "10.00",
                     expected_status=400)

    def test_cannot_send_to_merchant_user(self, client, full_seed_data):
        """A merchant admin user ID cannot be a receiver (role != 'user')."""
        u1_id, u1_email = MULTI_CONSUMERS[0]
        _, _, _, _, merchant_user_id = MULTI_MERCHANTS[0]
        headers = _consumer_headers(u1_id, u1_email)
        _wallet_send(client, headers, merchant_user_id, "10.00",
                     expected_status=400)

    def test_unauthenticated_request_returns_401(self, client, full_seed_data):
        """Requests without a token are rejected."""
        u2_id, _ = MULTI_CONSUMERS[1]
        resp = client.post("/wallet/send", json={
            "receiver_user_id": u2_id,
            "amount": "10.00",
            "idempotency_key": str(uuid.uuid4()),
        })
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 4. Idempotency
# ---------------------------------------------------------------------------

class TestWalletTransferIdempotency:

    def test_same_key_returns_same_transaction(self, client, full_seed_data):
        """Submitting the same key twice returns the same transaction."""
        u1_id, u1_email = MULTI_CONSUMERS[0]
        u2_id, _ = MULTI_CONSUMERS[1]
        key = str(uuid.uuid4())
        headers = _consumer_headers(u1_id, u1_email)
        r1 = _wallet_send(client, headers, u2_id, "10.00", key=key)
        r2 = _wallet_send(client, headers, u2_id, "10.00", key=key)
        assert r1["transaction_id"] == r2["transaction_id"]

    def test_different_keys_create_separate_transactions(self, client, full_seed_data):
        """Different idempotency keys always create new transactions."""
        u1_id, u1_email = MULTI_CONSUMERS[0]
        u2_id, _ = MULTI_CONSUMERS[1]
        with patch("app.services.description_service.generate_description",
                   return_value="x"):
            with patch("app.services.notification_service.notify_transaction"):
                headers = _consumer_headers(u1_id, u1_email)
                r1 = _wallet_send(client, headers, u2_id, "5.00")
                r2 = _wallet_send(client, headers, u2_id, "5.00")
                assert r1["transaction_id"] != r2["transaction_id"]


# ---------------------------------------------------------------------------
# 5. Description and notification
# ---------------------------------------------------------------------------

class TestWalletTransferDescriptionAndNotification:

    def test_description_generated_on_transfer(self, client, full_seed_data):
        """POST /wallet/send returns an AI-generated description."""
        u1_id, u1_email = MULTI_CONSUMERS[0]
        u2_id, _ = MULTI_CONSUMERS[1]
        with patch("app.services.description_service.generate_description",
                   return_value="Wallet transfer between friends"):
            headers = _consumer_headers(u1_id, u1_email)
            data = _wallet_send(client, headers, u2_id, "20.00")
            assert data["description"] == "Wallet transfer between friends"

    def test_notification_sent_to_receiver(self, client, full_seed_data):
        """notify_transaction is called with the receiver's user_id."""
        u1_id, u1_email = MULTI_CONSUMERS[0]
        u2_id, _ = MULTI_CONSUMERS[1]
        with patch("app.services.description_service.generate_description",
                   return_value="x"):
            with patch(
                "app.services.notification_service.notify_transaction"
            ) as mock_notify:
                headers = _consumer_headers(u1_id, u1_email)
                _wallet_send(client, headers, u2_id, "15.00")
                assert mock_notify.called
                # Second positional arg is the user_id — should be the RECEIVER
                assert mock_notify.call_args[0][1] == u2_id

    def test_user_provided_description_passed_through(self, client, full_seed_data):
        """A user-provided note is forwarded to description_service."""
        u1_id, u1_email = MULTI_CONSUMERS[0]
        u2_id, _ = MULTI_CONSUMERS[1]
        with patch(
            "app.services.description_service.generate_description",
            return_value="Splitting dinner"
        ) as mock_desc:
            headers = _consumer_headers(u1_id, u1_email)
            _wallet_send(client, headers, u2_id, "25.00",
                         description="Splitting dinner")
            assert mock_desc.call_args[0][3] == "Splitting dinner"


# ---------------------------------------------------------------------------
# 6. Transaction listing
# ---------------------------------------------------------------------------

class TestWalletTransferListing:

    def test_transfer_visible_in_receiver_listing(self, client, full_seed_data):
        """Received wallet transfers appear in the receiver's /payments list."""
        u1_id, u1_email = MULTI_CONSUMERS[0]
        u2_id, u2_email = MULTI_CONSUMERS[1]
        with patch("app.services.description_service.generate_description",
                   return_value="x"):
            with patch("app.services.notification_service.notify_transaction"):
                headers_sender = _consumer_headers(u1_id, u1_email)
                result = _wallet_send(client, headers_sender, u2_id, "10.00")
                txn_id = result["transaction_id"]

        headers_receiver = _consumer_headers(u2_id, u2_email)
        resp = client.get(f"/payments?user_id={u2_id}", headers=headers_receiver)
        assert resp.status_code == 200
        ids = [item["id"] for item in resp.json()["items"]]
        assert txn_id in ids

    def test_transfer_visible_in_sender_listing(self, client, full_seed_data):
        """Sent wallet transfers appear in the sender's /payments list."""
        u1_id, u1_email = MULTI_CONSUMERS[0]
        u2_id, _ = MULTI_CONSUMERS[1]
        with patch("app.services.description_service.generate_description",
                   return_value="x"):
            with patch("app.services.notification_service.notify_transaction"):
                headers = _consumer_headers(u1_id, u1_email)
                result = _wallet_send(client, headers, u2_id, "10.00")
                txn_id = result["transaction_id"]

        resp = client.get(f"/payments?user_id={u1_id}", headers=headers)
        assert resp.status_code == 200
        ids = [item["id"] for item in resp.json()["items"]]
        assert txn_id in ids
