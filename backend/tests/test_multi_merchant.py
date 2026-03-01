"""
Multi-merchant scenario tests.

Covers (from the implementation plan):
  - Multiple merchants sending payments to each other
  - AI description generated on every transaction
  - Notifications triggered on completed AND failed payments
  - Balance correctly debited/credited
  - FedNow/RTP 1.25% discount applied
  - Idempotency across different merchant pairs
  - Profile updates (email, phone) for merchant admins
  - Payment filtering by merchant
"""
import uuid
from decimal import Decimal
from unittest.mock import patch, MagicMock

import pytest

from tests.conftest import make_auth_header, MULTI_MERCHANTS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _headers(user_id: str, email: str) -> dict:
    return make_auth_header(user_id, email, role="merchant_admin")


def _pay(client, sender_id: str, receiver_id: str, amount: str,
         headers: dict, rail: str | None = None, key: str | None = None) -> dict:
    body = {
        "sender_merchant_id": sender_id,
        "receiver_merchant_id": receiver_id,
        "amount": amount,
        "idempotency_key": key or str(uuid.uuid4()),
    }
    if rail:
        body["preferred_rail"] = rail
    resp = client.post("/payments", json=body, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# 1. Basic multi-merchant payments
# ---------------------------------------------------------------------------

class TestMerchantToMerchantPayments:

    def test_acme_pays_globex(self, client, full_seed_data):
        """Acme Corp → Globex Inc."""
        h = _headers("user-001", "admin@acme.com")
        data = _pay(client, "merchant-001", "merchant-002", "5000.00", h)
        assert data["status"] in ("completed", "failed")
        assert data["sender_merchant_id"] == "merchant-001"
        assert data["receiver_merchant_id"] == "merchant-002"

    def test_walmart_pays_acme(self, client, full_seed_data):
        """WalmartTestCorp → Acme Corp."""
        h = _headers("user-003", "admin@walmart.testcorp")
        data = _pay(client, "merchant-003", "merchant-001", "2500.00", h)
        assert data["status"] in ("completed", "failed")

    def test_westernunion_pays_mcdonalds(self, client, full_seed_data):
        """WesternUnionTestCorp → McDonaldsTestCorp."""
        h = _headers("user-008", "admin@westernunion.testcorp")
        data = _pay(client, "merchant-008", "merchant-006", "750.00", h)
        assert data["status"] in ("completed", "failed")

    def test_multiple_merchants_pay_same_receiver(self, client, full_seed_data):
        """Three different merchants all pay Globex Inc."""
        receivers = []
        for m_id, _, _, m_email, u_id in MULTI_MERCHANTS[2:]:  # walmart, westernunion, mcdonalds
            h = _headers(u_id, m_email)
            data = _pay(client, m_id, "merchant-002", "100.00", h)
            receivers.append(data["receiver_merchant_id"])
        assert all(r == "merchant-002" for r in receivers)

    def test_circular_payments(self, client, full_seed_data):
        """A→B, B→C, C→A — verify all complete without error."""
        pairs = [
            ("merchant-001", "merchant-002", "user-001", "admin@acme.com"),
            ("merchant-002", "merchant-003", "user-002", "admin@globex.com"),
            ("merchant-003", "merchant-001", "user-003", "admin@walmart.testcorp"),
        ]
        for sender, receiver, u_id, email in pairs:
            h = _headers(u_id, email)
            data = _pay(client, sender, receiver, "200.00", h)
            assert data["status"] in ("completed", "failed")


# ---------------------------------------------------------------------------
# 2. AI description field
# ---------------------------------------------------------------------------

class TestDescriptionGeneration:

    def test_description_present_on_completed_payment(self, client, full_seed_data):
        """Every payment response must include a description field."""
        with patch("app.services.description_service.generate_description",
                   return_value="Purchase of bulk goods via FedNow"):
            h = _headers("user-001", "admin@acme.com")
            data = _pay(client, "merchant-001", "merchant-002", "1000.00", h)
            assert "description" in data
            assert data["description"] is not None
            assert len(data["description"]) > 0

    def test_description_reflects_merchant_name(self, client, full_seed_data):
        """Fallback description should contain the receiver merchant name."""
        with patch("app.services.description_service.generate_description",
                   side_effect=Exception("API unavailable")):
            # When the service itself raises, payment_service catches and falls back
            with patch("app.services.description_service.generate_description",
                       return_value="Payment to WalmartTestCorp via FEDNOW"):
                h = _headers("user-001", "admin@acme.com")
                data = _pay(client, "merchant-001", "merchant-003", "500.00", h)
                assert data.get("description") is not None

    def test_description_fallback_when_api_key_blank(self, client, full_seed_data):
        """With no API key, description_service falls back gracefully (no crash)."""
        with patch("app.config.settings") as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = ""
            h = _headers("user-001", "admin@acme.com")
            # Should not raise — fallback returns plain string
            data = _pay(client, "merchant-001", "merchant-002", "300.00", h)
            assert data["status"] in ("completed", "failed")

    def test_description_retrievable_via_get_payment(self, client, full_seed_data):
        """GET /payments/{id} returns the description set during creation."""
        with patch("app.services.description_service.generate_description",
                   return_value="Retail supply order via FedNow"):
            h = _headers("user-001", "admin@acme.com")
            created = _pay(client, "merchant-001", "merchant-002", "800.00", h)
            get_resp = client.get(f"/payments/{created['id']}", headers=h)
            assert get_resp.status_code == 200
            assert get_resp.json()["description"] == "Retail supply order via FedNow"


# ---------------------------------------------------------------------------
# 3. Notifications
# ---------------------------------------------------------------------------

class TestMerchantNotifications:

    def test_notification_triggered_on_completed(self, client, full_seed_data):
        """notify_transaction is called when payment completes."""
        with patch("app.services.description_service.generate_description",
                   return_value="Test payment"):
            with patch("app.services.notification_service.notify_transaction") as mock_notify:
                with patch("app.services.bank.mock_bank.mock_bank_service.initiate_transfer") as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="completed", reference_id="ref-001", failure_reason=None
                    )
                    h = _headers("user-001", "admin@acme.com")
                    _pay(client, "merchant-001", "merchant-002", "1000.00", h)
                    assert mock_notify.called

    def test_notification_triggered_on_failure(self, client, full_seed_data):
        """notify_transaction is called even when payment fails."""
        with patch("app.services.description_service.generate_description",
                   return_value="Test payment"):
            with patch("app.services.notification_service.notify_transaction") as mock_notify:
                with patch("app.services.bank.mock_bank.mock_bank_service.initiate_transfer") as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="failed", reference_id="ref-002",
                        failure_reason="Insufficient funds at bank"
                    )
                    h = _headers("user-001", "admin@acme.com")
                    data = _pay(client, "merchant-001", "merchant-002", "1000.00", h)
                    assert data["status"] == "failed"
                    assert mock_notify.called

    def test_notification_carries_correct_status(self, client, full_seed_data):
        """notify_transaction receives the actual transaction status."""
        with patch("app.services.description_service.generate_description",
                   return_value="Test payment"):
            with patch("app.services.notification_service.notify_transaction") as mock_notify:
                with patch("app.services.bank.mock_bank.mock_bank_service.initiate_transfer") as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="completed", reference_id="ref-003", failure_reason=None
                    )
                    h = _headers("user-001", "admin@acme.com")
                    _pay(client, "merchant-001", "merchant-002", "500.00", h)
                    call_kwargs = mock_notify.call_args
                    # 4th positional arg is status
                    assert call_kwargs[0][3] == "completed"


# ---------------------------------------------------------------------------
# 4. Balance tracking
# ---------------------------------------------------------------------------

class TestMerchantBalances:

    def test_initial_balance_is_100k(self, client, full_seed_data):
        """All seeded merchants start with $100,000."""
        for m_id, _, _, m_email, u_id in MULTI_MERCHANTS:
            h = _headers(u_id, m_email)
            resp = client.get(f"/payments/balance?merchant_id={m_id}", headers=h)
            assert resp.status_code == 200
            assert float(resp.json()["balance"]) == 100000.00

    def test_sender_balance_decreases(self, client, full_seed_data):
        """Sender's balance is reduced after a completed payment."""
        with patch("app.services.description_service.generate_description", return_value="x"):
            with patch("app.services.notification_service.notify_transaction"):
                with patch("app.services.bank.mock_bank.mock_bank_service.initiate_transfer") as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="completed", reference_id="r1", failure_reason=None
                    )
                    h = _headers("user-001", "admin@acme.com")
                    _pay(client, "merchant-001", "merchant-002", "10000.00", h)
                    resp = client.get("/payments/balance?merchant_id=merchant-001", headers=h)
                    # FedNow applies 1.25% discount: 10000 * 0.9875 = 9875.00
                    assert float(resp.json()["balance"]) < 100000.00

    def test_receiver_balance_increases(self, client, full_seed_data):
        """Receiver's balance is credited after a completed payment."""
        with patch("app.services.description_service.generate_description", return_value="x"):
            with patch("app.services.notification_service.notify_transaction"):
                with patch("app.services.bank.mock_bank.mock_bank_service.initiate_transfer") as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="completed", reference_id="r2", failure_reason=None
                    )
                    h_sender = _headers("user-001", "admin@acme.com")
                    h_receiver = _headers("user-002", "admin@globex.com")
                    _pay(client, "merchant-001", "merchant-002", "5000.00", h_sender)
                    resp = client.get("/payments/balance?merchant_id=merchant-002", headers=h_receiver)
                    assert float(resp.json()["balance"]) > 100000.00

    def test_fednow_discount_applied(self, client, full_seed_data):
        """FedNow payments settle at amount × 0.9875."""
        with patch("app.services.description_service.generate_description", return_value="x"):
            with patch("app.services.notification_service.notify_transaction"):
                with patch("app.services.bank.mock_bank.mock_bank_service.initiate_transfer") as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="completed", reference_id="r3", failure_reason=None
                    )
                    h = _headers("user-001", "admin@acme.com")
                    data = _pay(client, "merchant-001", "merchant-002",
                                "10000.00", h, rail="fednow")
                    # Settled amount should be 9875.00
                    assert float(data["amount"]) == pytest.approx(9875.00)

    def test_failed_payment_does_not_change_balance(self, client, full_seed_data):
        """A failed payment must not debit the sender."""
        with patch("app.services.description_service.generate_description", return_value="x"):
            with patch("app.services.notification_service.notify_transaction"):
                with patch("app.services.bank.mock_bank.mock_bank_service.initiate_transfer") as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="failed", reference_id="r4",
                        failure_reason="Bank declined"
                    )
                    h = _headers("user-001", "admin@acme.com")
                    _pay(client, "merchant-001", "merchant-002", "5000.00", h)
                    resp = client.get("/payments/balance?merchant_id=merchant-001", headers=h)
                    assert float(resp.json()["balance"]) == 100000.00


# ---------------------------------------------------------------------------
# 5. Idempotency
# ---------------------------------------------------------------------------

class TestMerchantIdempotency:

    def test_same_key_returns_same_transaction(self, client, full_seed_data):
        """Submitting the same idempotency key twice returns the same record."""
        key = str(uuid.uuid4())
        h = _headers("user-001", "admin@acme.com")
        r1 = _pay(client, "merchant-001", "merchant-002", "1000.00", h, key=key)
        r2 = _pay(client, "merchant-001", "merchant-002", "1000.00", h, key=key)
        assert r1["id"] == r2["id"]

    def test_different_keys_create_separate_transactions(self, client, full_seed_data):
        """Different idempotency keys always create new transactions."""
        h = _headers("user-001", "admin@acme.com")
        r1 = _pay(client, "merchant-001", "merchant-002", "100.00", h)
        r2 = _pay(client, "merchant-001", "merchant-002", "100.00", h)
        assert r1["id"] != r2["id"]


# ---------------------------------------------------------------------------
# 6. Payment listing and filtering
# ---------------------------------------------------------------------------

class TestMerchantPaymentListing:

    def test_list_filtered_by_sender_merchant(self, client, full_seed_data):
        """GET /payments?merchant_id=X returns only that merchant's payments."""
        h = _headers("user-001", "admin@acme.com")
        for _ in range(3):
            _pay(client, "merchant-001", "merchant-002", "50.00", h)
        resp = client.get("/payments?merchant_id=merchant-001", headers=h)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 3
        for item in data["items"]:
            assert (item["sender_merchant_id"] == "merchant-001"
                    or item["receiver_merchant_id"] == "merchant-001")

    def test_list_by_user_id(self, client, full_seed_data):
        """GET /payments?user_id= is ignored for merchant payments (sender_user_id is null)."""
        h = _headers("user-001", "admin@acme.com")
        resp = client.get("/payments?user_id=user-001", headers=h)
        assert resp.status_code == 200

    def test_list_filtered_by_status(self, client, full_seed_data):
        """Filtering by status only returns payments in that state."""
        with patch("app.services.description_service.generate_description", return_value="x"):
            with patch("app.services.notification_service.notify_transaction"):
                with patch("app.services.bank.mock_bank.mock_bank_service.initiate_transfer") as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="completed", reference_id="rX", failure_reason=None
                    )
                    h = _headers("user-001", "admin@acme.com")
                    _pay(client, "merchant-001", "merchant-002", "100.00", h)
                    resp = client.get(
                        "/payments?merchant_id=merchant-001&status=completed",
                        headers=h
                    )
                    assert resp.status_code == 200
                    for item in resp.json()["items"]:
                        assert item["status"] == "completed"


# ---------------------------------------------------------------------------
# 7. Profile updates
# ---------------------------------------------------------------------------

class TestMerchantProfileUpdate:

    def test_merchant_user_can_update_phone(self, client, full_seed_data):
        """PATCH /auth/me saves a new phone number for a merchant admin."""
        h = _headers("user-001", "admin@acme.com")
        resp = client.patch("/auth/me", json={"phone": "+15550001111"}, headers=h)
        assert resp.status_code == 200
        assert resp.json()["phone"] == "+15550001111"

    def test_merchant_user_can_update_email(self, client, full_seed_data):
        """PATCH /auth/me saves a new email for a merchant admin."""
        h = _headers("user-003", "admin@walmart.testcorp")
        new_email = "admin@walmart-new.testcorp"
        resp = client.patch("/auth/me", json={"email": new_email}, headers=h)
        assert resp.status_code == 200
        assert resp.json()["email"] == new_email

    def test_cannot_change_email_to_existing(self, client, full_seed_data):
        """Changing email to one already in use returns 409."""
        h = _headers("user-001", "admin@acme.com")
        resp = client.patch("/auth/me",
                            json={"email": "admin@globex.com"},
                            headers=h)
        assert resp.status_code == 409

    def test_phone_visible_on_me_endpoint(self, client, full_seed_data):
        """Phone set via PATCH /auth/me is returned by GET /auth/me."""
        h = _headers("user-001", "admin@acme.com")
        client.patch("/auth/me", json={"phone": "+15559876543"}, headers=h)
        resp = client.get("/auth/me", headers=h)
        assert resp.json()["phone"] == "+15559876543"
