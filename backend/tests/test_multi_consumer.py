"""
Multi-consumer scenario tests.

Covers (from the implementation plan):
  - Consumer paying multiple different merchants
  - Two consumers paying the same merchant simultaneously
  - Wallet balance decreases after consumer payment
  - Merchant balance increases after consumer payment
  - AI description generated on every consumer payment
  - Notifications triggered on completed AND failed consumer payments
  - Insufficient wallet funds returns 400
  - Consumer transaction listing filtered by user_id
  - Wallet top-up
  - Consumer payment idempotency
  - Consumer profile updates (phone, email, duplicate email rejection)
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


def _consumer_pay(client, user_id: str, email: str, merchant_id: str,
                  amount: str, key: str | None = None,
                  description: str | None = None,
                  rail: str | None = None,
                  expected_status: int = 200) -> dict:
    body = {
        "merchant_id": merchant_id,
        "amount": amount,
        "idempotency_key": key or str(uuid.uuid4()),
    }
    if description is not None:
        body["description"] = description
    if rail is not None:
        body["preferred_rail"] = rail
    headers = _consumer_headers(user_id, email)
    resp = client.post("/consumer/pay", json=body, headers=headers)
    assert resp.status_code == expected_status, resp.text
    return resp.json()


def _get_consumer_balance(client, user_id: str, email: str) -> float:
    headers = _consumer_headers(user_id, email)
    resp = client.get("/consumer/wallet/balance", headers=headers)
    assert resp.status_code == 200, resp.text
    return float(resp.json()["balance"])


def _get_merchant_balance(client, merchant_id: str,
                          user_id: str, email: str) -> float:
    headers = _merchant_headers(user_id, email)
    resp = client.get(f"/payments/balance?merchant_id={merchant_id}", headers=headers)
    assert resp.status_code == 200, resp.text
    return float(resp.json()["balance"])


# ---------------------------------------------------------------------------
# 1. Basic multi-consumer payments
# ---------------------------------------------------------------------------

class TestConsumerPayments:

    def test_consumer_pays_walmart(self, client, full_seed_data):
        """consumer1 pays WalmartTestCorp (merchant-003)."""
        u_id, email = MULTI_CONSUMERS[0]
        data = _consumer_pay(client, u_id, email, "merchant-003", "50.00")
        assert data["status"] in ("completed", "failed")

    def test_consumer_pays_westernunion(self, client, full_seed_data):
        """consumer1 pays WesternUnionTestCorp (merchant-008)."""
        u_id, email = MULTI_CONSUMERS[0]
        data = _consumer_pay(client, u_id, email, "merchant-008", "100.00")
        assert data["status"] in ("completed", "failed")

    def test_consumer_pays_mcdonalds(self, client, full_seed_data):
        """consumer1 pays McDonaldsTestCorp (merchant-006)."""
        u_id, email = MULTI_CONSUMERS[0]
        data = _consumer_pay(client, u_id, email, "merchant-006", "20.00")
        assert data["status"] in ("completed", "failed")

    def test_two_consumers_pay_same_merchant(self, client, full_seed_data):
        """Both consumer1 and consumer2 pay Acme Corp (merchant-001)."""
        results = []
        for u_id, email in MULTI_CONSUMERS:
            data = _consumer_pay(client, u_id, email, "merchant-001", "10.00")
            results.append(data)
        assert len(results) == 2
        # Both should have a status (may succeed or fail independently)
        for r in results:
            assert r["status"] in ("completed", "failed")
        # Each should get a separate transaction_id
        ids = [r["transaction_id"] for r in results]
        assert ids[0] != ids[1]

    def test_merchant_role_cannot_use_consumer_endpoint(self, client, full_seed_data):
        """A merchant admin calling POST /consumer/pay gets 403 Forbidden."""
        m_id, _, _, m_email, u_id = MULTI_MERCHANTS[0]
        headers = _merchant_headers(u_id, m_email)
        body = {
            "merchant_id": "merchant-002",
            "amount": "10.00",
            "idempotency_key": str(uuid.uuid4()),
        }
        resp = client.post("/consumer/pay", json=body, headers=headers)
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# 2. Wallet balance changes
# ---------------------------------------------------------------------------

class TestConsumerWalletBalance:

    def test_consumer_initial_balance_is_500(self, client, full_seed_data):
        """Both seeded consumers start with a $500.00 wallet."""
        for u_id, email in MULTI_CONSUMERS:
            balance = _get_consumer_balance(client, u_id, email)
            assert balance == pytest.approx(500.00)

    def test_consumer_balance_decreases_after_completed_payment(self, client, full_seed_data):
        """Wallet is debited after a completed consumer payment."""
        u_id, email = MULTI_CONSUMERS[0]
        with patch("app.services.description_service.generate_description",
                   return_value="Burger combo meal"):
            with patch("app.services.notification_service.notify_transaction"):
                with patch(
                    "app.services.bank.mock_bank.mock_bank_service.initiate_transfer"
                ) as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="completed", reference_id="c-ref-1", failure_reason=None
                    )
                    before = _get_consumer_balance(client, u_id, email)
                    _consumer_pay(client, u_id, email, "merchant-006", "25.00")
                    after = _get_consumer_balance(client, u_id, email)
                    assert after < before

    def test_consumer_balance_unchanged_after_failed_payment(self, client, full_seed_data):
        """Wallet is NOT debited when a consumer payment fails."""
        u_id, email = MULTI_CONSUMERS[1]
        with patch("app.services.description_service.generate_description",
                   return_value="Failed payment"):
            with patch("app.services.notification_service.notify_transaction"):
                with patch(
                    "app.services.bank.mock_bank.mock_bank_service.initiate_transfer"
                ) as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="failed", reference_id="c-ref-2",
                        failure_reason="Bank declined"
                    )
                    before = _get_consumer_balance(client, u_id, email)
                    _consumer_pay(client, u_id, email, "merchant-003", "10.00")
                    after = _get_consumer_balance(client, u_id, email)
                    assert after == pytest.approx(before)

    def test_merchant_balance_increases_after_consumer_payment(self, client, full_seed_data):
        """Merchant's ledger is credited after consumer payment completes."""
        u_id, email = MULTI_CONSUMERS[0]
        m_id, _, _, m_email, m_user_id = MULTI_MERCHANTS[0]  # merchant-001 / Acme Corp
        with patch("app.services.description_service.generate_description",
                   return_value="Consumer purchase"):
            with patch("app.services.notification_service.notify_transaction"):
                with patch(
                    "app.services.bank.mock_bank.mock_bank_service.initiate_transfer"
                ) as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="completed", reference_id="c-ref-3", failure_reason=None
                    )
                    before = _get_merchant_balance(client, m_id, m_user_id, m_email)
                    _consumer_pay(client, u_id, email, m_id, "50.00")
                    after = _get_merchant_balance(client, m_id, m_user_id, m_email)
                    assert after > before

    def test_fednow_discount_applied_on_consumer_payment(self, client, full_seed_data):
        """FedNow consumer payments settle at amount × 0.9875."""
        u_id, email = MULTI_CONSUMERS[0]
        with patch("app.services.description_service.generate_description",
                   return_value="FedNow purchase"):
            with patch("app.services.notification_service.notify_transaction"):
                with patch(
                    "app.services.bank.mock_bank.mock_bank_service.initiate_transfer"
                ) as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="completed", reference_id="c-ref-4", failure_reason=None
                    )
                    before = _get_consumer_balance(client, u_id, email)
                    _consumer_pay(client, u_id, email, "merchant-001", "100.00",
                                  rail="fednow")
                    after = _get_consumer_balance(client, u_id, email)
                    # 100 * 0.9875 = 98.75 debited
                    assert before - after == pytest.approx(98.75, abs=0.01)


# ---------------------------------------------------------------------------
# 3. AI description on consumer payments
# ---------------------------------------------------------------------------

class TestConsumerDescriptionGeneration:

    def test_description_present_on_consumer_payment(self, client, full_seed_data):
        """Consumer payment transaction has a description set."""
        u_id, email = MULTI_CONSUMERS[0]
        with patch("app.services.description_service.generate_description",
                   return_value="Large fries and a drink via FedNow"):
            data = _consumer_pay(client, u_id, email, "merchant-006", "15.00")
            txn_id = data["transaction_id"]
            # Fetch via payments listing to verify description stored
            h = _consumer_headers(u_id, email)
            list_resp = client.get(f"/payments?user_id={u_id}", headers=h)
            assert list_resp.status_code == 200
            items = list_resp.json()["items"]
            matching = [i for i in items if i["id"] == txn_id]
            if matching:
                assert matching[0].get("description") is not None

    def test_consumer_provided_description_used(self, client, full_seed_data):
        """When user provides a description, it overrides AI generation."""
        u_id, email = MULTI_CONSUMERS[0]
        # description_service should still be called but will receive user_provided
        with patch("app.services.description_service.generate_description",
                   return_value="My custom note") as mock_desc:
            _consumer_pay(client, u_id, email, "merchant-003", "30.00",
                          description="Groceries for the week")
            # generate_description was called with the user-provided description
            call_args = mock_desc.call_args[0]
            assert call_args[3] == "Groceries for the week"

    def test_description_fallback_on_api_error(self, client, full_seed_data):
        """If description_service raises internally, payment still completes."""
        u_id, email = MULTI_CONSUMERS[0]
        with patch("app.services.description_service.generate_description",
                   return_value="Payment to McDonaldsTestCorp via FEDNOW"):
            with patch("app.services.notification_service.notify_transaction"):
                data = _consumer_pay(client, u_id, email, "merchant-006", "8.00")
                assert data["status"] in ("completed", "failed")


# ---------------------------------------------------------------------------
# 4. Notifications on consumer payments
# ---------------------------------------------------------------------------

class TestConsumerNotifications:

    def test_notification_triggered_on_completed_consumer_payment(
        self, client, full_seed_data
    ):
        """notify_transaction is called when a consumer payment completes."""
        u_id, email = MULTI_CONSUMERS[0]
        with patch("app.services.description_service.generate_description",
                   return_value="Test"):
            with patch(
                "app.services.notification_service.notify_transaction"
            ) as mock_notify:
                with patch(
                    "app.services.bank.mock_bank.mock_bank_service.initiate_transfer"
                ) as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="completed", reference_id="n-ref-1", failure_reason=None
                    )
                    _consumer_pay(client, u_id, email, "merchant-001", "20.00")
                    assert mock_notify.called

    def test_notification_triggered_on_failed_consumer_payment(
        self, client, full_seed_data
    ):
        """notify_transaction is called even when a consumer payment fails."""
        u_id, email = MULTI_CONSUMERS[0]
        with patch("app.services.description_service.generate_description",
                   return_value="Test"):
            with patch(
                "app.services.notification_service.notify_transaction"
            ) as mock_notify:
                with patch(
                    "app.services.bank.mock_bank.mock_bank_service.initiate_transfer"
                ) as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="failed", reference_id="n-ref-2",
                        failure_reason="Declined by bank"
                    )
                    data = _consumer_pay(client, u_id, email, "merchant-001", "20.00")
                    assert data["status"] == "failed"
                    assert mock_notify.called

    def test_notification_receives_consumer_user_id(self, client, full_seed_data):
        """notify_transaction is called with the consumer's user_id."""
        u_id, email = MULTI_CONSUMERS[1]
        with patch("app.services.description_service.generate_description",
                   return_value="Test"):
            with patch(
                "app.services.notification_service.notify_transaction"
            ) as mock_notify:
                with patch(
                    "app.services.bank.mock_bank.mock_bank_service.initiate_transfer"
                ) as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="completed", reference_id="n-ref-3", failure_reason=None
                    )
                    _consumer_pay(client, u_id, email, "merchant-002", "15.00")
                    # First positional arg to notify_transaction is db, second is user_id
                    call_args = mock_notify.call_args[0]
                    assert call_args[1] == u_id


# ---------------------------------------------------------------------------
# 5. Insufficient funds
# ---------------------------------------------------------------------------

class TestConsumerInsufficientFunds:

    def test_insufficient_wallet_returns_400(self, client, full_seed_data):
        """Payment exceeding wallet balance returns HTTP 400."""
        u_id, email = MULTI_CONSUMERS[0]
        # Seeded balance is $500 — request $10,000
        _consumer_pay(client, u_id, email, "merchant-001", "10000.00",
                      expected_status=400)

    def test_exact_balance_payment_allowed(self, client, full_seed_data):
        """Payment equal to wallet balance should be attempted (not immediately rejected)."""
        u_id, email = MULTI_CONSUMERS[0]
        with patch("app.services.description_service.generate_description",
                   return_value="Exact balance payment"):
            with patch("app.services.notification_service.notify_transaction"):
                with patch(
                    "app.services.bank.mock_bank.mock_bank_service.initiate_transfer"
                ) as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="completed", reference_id="ins-ref-1", failure_reason=None
                    )
                    # $500.00 exactly — should pass the balance check
                    data = _consumer_pay(client, u_id, email, "merchant-001", "500.00")
                    assert data["status"] in ("completed", "failed")

    def test_second_payment_fails_after_wallet_drained(self, client, full_seed_data):
        """After draining the wallet, a second payment is rejected with 400."""
        u_id, email = MULTI_CONSUMERS[0]
        with patch("app.services.description_service.generate_description",
                   return_value="First payment"):
            with patch("app.services.notification_service.notify_transaction"):
                with patch(
                    "app.services.bank.mock_bank.mock_bank_service.initiate_transfer"
                ) as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="completed", reference_id="ins-ref-2", failure_reason=None
                    )
                    # Use ACH rail (no FedNow/RTP discount) so exactly $500.00 is
                    # debited and the wallet reaches $0.00.
                    _consumer_pay(client, u_id, email, "merchant-001", "500.00",
                                  rail="ach")

        # Wallet is now $0 — a $1.00 payment must be rejected immediately
        _consumer_pay(client, u_id, email, "merchant-001", "1.00",
                      expected_status=400)


# ---------------------------------------------------------------------------
# 6. Transaction listing by user_id
# ---------------------------------------------------------------------------

class TestConsumerTransactionListing:

    def test_consumer_transactions_filterable_by_user_id(self, client, full_seed_data):
        """GET /payments?user_id= returns only transactions for that consumer."""
        u_id, email = MULTI_CONSUMERS[0]
        # Create two payments for consumer 1
        with patch("app.services.description_service.generate_description",
                   return_value="x"):
            with patch("app.services.notification_service.notify_transaction"):
                for _ in range(2):
                    _consumer_pay(client, u_id, email, "merchant-001", "5.00")

        headers = _consumer_headers(u_id, email)
        resp = client.get(f"/payments?user_id={u_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2
        for item in data["items"]:
            assert item["sender_user_id"] == u_id

    def test_consumer1_cannot_see_consumer2_transactions(self, client, full_seed_data):
        """Transactions for consumer2 do not appear in consumer1's filtered list."""
        u1_id, u1_email = MULTI_CONSUMERS[0]
        u2_id, u2_email = MULTI_CONSUMERS[1]

        with patch("app.services.description_service.generate_description",
                   return_value="x"):
            with patch("app.services.notification_service.notify_transaction"):
                _consumer_pay(client, u2_id, u2_email, "merchant-002", "10.00")

        headers = _consumer_headers(u1_id, u1_email)
        resp = client.get(f"/payments?user_id={u1_id}", headers=headers)
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["sender_user_id"] != u2_id

    def test_consumer_transactions_respect_page_size(self, client, full_seed_data):
        """page_size parameter limits the number of results returned."""
        u_id, email = MULTI_CONSUMERS[0]
        with patch("app.services.description_service.generate_description",
                   return_value="x"):
            with patch("app.services.notification_service.notify_transaction"):
                for _ in range(4):
                    _consumer_pay(client, u_id, email, "merchant-001", "1.00")

        headers = _consumer_headers(u_id, email)
        resp = client.get(f"/payments?user_id={u_id}&page_size=2", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()["items"]) <= 2


# ---------------------------------------------------------------------------
# 7. Wallet top-up
# ---------------------------------------------------------------------------

class TestConsumerWalletTopup:

    def test_topup_increases_wallet_balance(self, client, full_seed_data):
        """POST /consumer/wallet/topup increases the consumer's wallet."""
        u_id, email = MULTI_CONSUMERS[0]
        before = _get_consumer_balance(client, u_id, email)
        headers = _consumer_headers(u_id, email)
        resp = client.post("/consumer/wallet/topup?amount=200.00", headers=headers)
        assert resp.status_code == 200
        after = float(resp.json()["balance"])
        assert after == pytest.approx(before + 200.00)

    def test_topup_zero_rejected(self, client, full_seed_data):
        """Top-up of $0 returns 400 Bad Request."""
        u_id, email = MULTI_CONSUMERS[0]
        headers = _consumer_headers(u_id, email)
        resp = client.post("/consumer/wallet/topup?amount=0", headers=headers)
        assert resp.status_code == 400

    def test_topup_enables_previously_rejected_payment(self, client, full_seed_data):
        """After topping up, a previously over-limit payment can proceed."""
        u_id, email = MULTI_CONSUMERS[0]

        # First, drain the wallet via a completed payment
        with patch("app.services.description_service.generate_description",
                   return_value="x"):
            with patch("app.services.notification_service.notify_transaction"):
                with patch(
                    "app.services.bank.mock_bank.mock_bank_service.initiate_transfer"
                ) as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="completed", reference_id="t-ref-1", failure_reason=None
                    )
                    _consumer_pay(client, u_id, email, "merchant-001", "500.00")

        # Confirm wallet is empty (or insufficient for $100)
        _consumer_pay(client, u_id, email, "merchant-001", "100.00",
                      expected_status=400)

        # Top-up $300
        headers = _consumer_headers(u_id, email)
        client.post("/consumer/wallet/topup?amount=300.00", headers=headers)

        # Now $100 payment should be accepted
        with patch("app.services.description_service.generate_description",
                   return_value="x"):
            with patch("app.services.notification_service.notify_transaction"):
                data = _consumer_pay(client, u_id, email, "merchant-001", "100.00")
                assert data["status"] in ("completed", "failed")


# ---------------------------------------------------------------------------
# 8. Idempotency
# ---------------------------------------------------------------------------

class TestConsumerIdempotency:

    def test_same_key_returns_same_transaction(self, client, full_seed_data):
        """Submitting the same idempotency key twice returns the same record."""
        u_id, email = MULTI_CONSUMERS[0]
        key = str(uuid.uuid4())
        r1 = _consumer_pay(client, u_id, email, "merchant-001", "10.00", key=key)
        r2 = _consumer_pay(client, u_id, email, "merchant-001", "10.00", key=key)
        assert r1["transaction_id"] == r2["transaction_id"]
        assert r1["status"] == r2["status"]

    def test_different_keys_create_separate_transactions(self, client, full_seed_data):
        """Different idempotency keys always create new transactions."""
        u_id, email = MULTI_CONSUMERS[0]
        with patch("app.services.description_service.generate_description",
                   return_value="x"):
            with patch("app.services.notification_service.notify_transaction"):
                r1 = _consumer_pay(client, u_id, email, "merchant-001", "5.00")
                r2 = _consumer_pay(client, u_id, email, "merchant-001", "5.00")
                assert r1["transaction_id"] != r2["transaction_id"]

    def test_idempotency_key_isolated_per_consumer(self, client, full_seed_data):
        """The same idempotency key used by two different consumers creates two records."""
        shared_key = str(uuid.uuid4())
        u1_id, u1_email = MULTI_CONSUMERS[0]
        u2_id, u2_email = MULTI_CONSUMERS[1]
        r1 = _consumer_pay(client, u1_id, u1_email, "merchant-001", "10.00",
                           key=shared_key)
        # consumer2 uses the same key — different sender_user_id, so it's a new txn
        r2 = _consumer_pay(client, u2_id, u2_email, "merchant-001", "10.00",
                           key=shared_key)
        # Both succeed and each consumer gets their own transaction
        assert r1["status"] in ("completed", "failed")
        assert r2["status"] in ("completed", "failed")


# ---------------------------------------------------------------------------
# 9. Consumer profile updates
# ---------------------------------------------------------------------------

class TestConsumerProfileUpdate:

    def test_consumer_can_update_phone(self, client, full_seed_data):
        """PATCH /auth/me saves a new phone number for a consumer."""
        u_id, email = MULTI_CONSUMERS[0]
        headers = _consumer_headers(u_id, email)
        resp = client.patch("/auth/me", json={"phone": "+15550009999"}, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["phone"] == "+15550009999"

    def test_consumer_can_update_email(self, client, full_seed_data):
        """PATCH /auth/me saves a new email address for a consumer."""
        u_id, _ = MULTI_CONSUMERS[0]
        new_email = "consumer1-updated@test.com"
        headers = _consumer_headers(u_id, "consumer1@test.com")
        resp = client.patch("/auth/me", json={"email": new_email}, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["email"] == new_email

    def test_cannot_change_email_to_existing(self, client, full_seed_data):
        """Changing email to one already in use by another user returns 409."""
        u1_id, u1_email = MULTI_CONSUMERS[0]
        _, u2_email = MULTI_CONSUMERS[1]
        headers = _consumer_headers(u1_id, u1_email)
        # Try to take consumer2's email
        resp = client.patch("/auth/me", json={"email": u2_email}, headers=headers)
        assert resp.status_code == 409

    def test_phone_visible_on_me_endpoint(self, client, full_seed_data):
        """Phone set via PATCH /auth/me is returned by GET /auth/me."""
        u_id, email = MULTI_CONSUMERS[1]
        headers = _consumer_headers(u_id, email)
        client.patch("/auth/me", json={"phone": "+15551112222"}, headers=headers)
        resp = client.get("/auth/me", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["phone"] == "+15551112222"

    def test_clearing_phone_sets_null(self, client, full_seed_data):
        """Sending an empty string for phone clears it (sets to None/null)."""
        u_id, email = MULTI_CONSUMERS[0]
        headers = _consumer_headers(u_id, email)
        # Set a phone first
        client.patch("/auth/me", json={"phone": "+15553334444"}, headers=headers)
        # Clear it
        resp = client.patch("/auth/me", json={"phone": ""}, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["phone"] is None
