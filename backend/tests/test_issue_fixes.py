"""
Tests verifying that all 4 issues from the fix plan are resolved.

Issue 1  — Clipboard copy fallback on HTTP
          Tested in Flutter: mobile_flutter/test/clipboard_helper_test.dart
          (requires browser/platform interaction; covered by widget tests)

Issue 2  — Dangerous keyword anomaly check
          Tested in Flutter: mobile_flutter/test/anomaly_detection_test.dart
          (pure Dart logic; covered by unit tests)

Issue 3  — SMS sender name ≤ 11 chars; improved error logging
          Covered here: TestIssue3SmsSender

Issue 4  — Consumer first_name / last_name columns
          Covered here: TestIssue4UserNameModel, TestIssue4PatchMe,
          TestIssue4PaymentNameEnrichment
"""

import inspect
import uuid
from decimal import Decimal

import pytest

from tests.conftest import get_auth_header
from app.models.user import User
from app.services.auth_service import hash_password, create_access_token
from app.services.wallet_service import wallet_credit


# ============================================================
# Issue 3 — SMS sender name
# ============================================================

class TestIssue3SmsSender:
    """BREVO_SMS_SENDER must be ≤ 11 chars; error logs must include response body."""

    def test_brevo_sms_sender_at_most_11_chars(self):
        """Brevo rejects alphanumeric sender IDs longer than 11 characters."""
        from app.config import settings
        sender = settings.BREVO_SMS_SENDER
        assert sender is not None, "BREVO_SMS_SENDER not configured in .env"
        assert len(sender) <= 11, (
            f"BREVO_SMS_SENDER '{sender}' is {len(sender)} chars; "
            f"Brevo requires ≤ 11 chars for alphanumeric sender IDs"
        )

    def test_brevo_sms_sender_is_payrails(self):
        """Sender name should be the corrected 'PayRails' value."""
        from app.config import settings
        assert settings.BREVO_SMS_SENDER == "PayRails"

    def test_sms_error_log_includes_response_body(self):
        """_send_sms must log the Brevo HTTP response body so the real rejection
        reason is visible in uvicorn logs (not just the exception message)."""
        from app.services import notification_service
        source = inspect.getsource(notification_service._send_sms)
        assert "response_body" in source, (
            "_send_sms should capture response_body for improved error logging"
        )

    def test_sms_improved_logging_branches_on_response_body(self):
        """The improved log path must log both the exception and the response body."""
        from app.services import notification_service
        source = inspect.getsource(notification_service._send_sms)
        # Both pieces of context should appear in the same log call
        assert "Brevo response" in source, (
            "_send_sms warning log should reference 'Brevo response' body"
        )


# ============================================================
# Issue 4 — User model columns
# ============================================================

class TestIssue4UserNameModel:
    """User ORM model must persist first_name and last_name."""

    def test_first_name_column_persists(self, db_session):
        u = User(id="cn-1", email="cn1@test.com",
                 hashed_password=hash_password("x"), role="user",
                 first_name="Alice")
        db_session.add(u)
        db_session.commit()
        fetched = db_session.query(User).filter(User.id == "cn-1").first()
        assert fetched.first_name == "Alice"

    def test_last_name_column_persists(self, db_session):
        u = User(id="cn-2", email="cn2@test.com",
                 hashed_password=hash_password("x"), role="user",
                 last_name="Smith")
        db_session.add(u)
        db_session.commit()
        fetched = db_session.query(User).filter(User.id == "cn-2").first()
        assert fetched.last_name == "Smith"

    def test_name_columns_nullable(self, db_session):
        u = User(id="cn-3", email="cn3@test.com",
                 hashed_password=hash_password("x"), role="user")
        db_session.add(u)
        db_session.commit()
        fetched = db_session.query(User).filter(User.id == "cn-3").first()
        assert fetched.first_name is None
        assert fetched.last_name is None

    def test_both_name_columns_persist_together(self, db_session):
        u = User(id="cn-4", email="cn4@test.com",
                 hashed_password=hash_password("x"), role="user",
                 first_name="Raja", last_name="Singh")
        db_session.add(u)
        db_session.commit()
        fetched = db_session.query(User).filter(User.id == "cn-4").first()
        assert fetched.first_name == "Raja"
        assert fetched.last_name == "Singh"


# ============================================================
# Issue 4 — PATCH /auth/me stores name fields
# ============================================================

class TestIssue4PatchMe:
    """PATCH /auth/me must accept and return first_name / last_name."""

    def _register_login(self, client, email, password="pass123"):
        client.post("/auth/register", json={"email": email, "password": password})
        r = client.post("/auth/login", json={"email": email, "password": password})
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    def test_patch_saves_both_names(self, client):
        h = self._register_login(client, "both@test.com")
        resp = client.patch("/auth/me",
                            json={"first_name": "Raja", "last_name": "Singh"},
                            headers=h)
        assert resp.status_code == 200
        data = resp.json()
        assert data["first_name"] == "Raja"
        assert data["last_name"] == "Singh"

    def test_get_me_returns_saved_names(self, client):
        h = self._register_login(client, "getname@test.com")
        client.patch("/auth/me",
                     json={"first_name": "Alice", "last_name": "Jones"},
                     headers=h)
        resp = client.get("/auth/me", headers=h)
        assert resp.json()["first_name"] == "Alice"
        assert resp.json()["last_name"] == "Jones"

    def test_patch_first_name_only(self, client):
        h = self._register_login(client, "fnonly@test.com")
        resp = client.patch("/auth/me", json={"first_name": "Bob"}, headers=h)
        assert resp.status_code == 200
        assert resp.json()["first_name"] == "Bob"
        assert resp.json()["last_name"] is None

    def test_new_user_has_null_names(self, client):
        h = self._register_login(client, "nullname@test.com")
        resp = client.get("/auth/me", headers=h)
        assert resp.json().get("first_name") is None
        assert resp.json().get("last_name") is None

    def test_patch_strips_whitespace(self, client):
        h = self._register_login(client, "ws@test.com")
        resp = client.patch("/auth/me",
                            json={"first_name": "  Jane  ", "last_name": "  Doe  "},
                            headers=h)
        assert resp.json()["first_name"] == "Jane"
        assert resp.json()["last_name"] == "Doe"

    def test_patch_empty_string_clears_name(self, client):
        h = self._register_login(client, "clear@test.com")
        client.patch("/auth/me", json={"first_name": "ToRemove"}, headers=h)
        resp = client.patch("/auth/me", json={"first_name": ""}, headers=h)
        assert resp.json()["first_name"] is None

    def test_patch_name_does_not_affect_email(self, client):
        h = self._register_login(client, "unchanged@test.com")
        client.patch("/auth/me",
                     json={"first_name": "Bob", "last_name": "Jones"},
                     headers=h)
        resp = client.get("/auth/me", headers=h)
        assert resp.json()["email"] == "unchanged@test.com"

    def test_patch_name_and_phone_together(self, client):
        """Name and phone can be updated in the same PATCH call."""
        h = self._register_login(client, "combo@test.com")
        resp = client.patch("/auth/me", json={
            "first_name": "Combo",
            "last_name": "User",
            "phone": "+15550009999",
        }, headers=h)
        assert resp.status_code == 200
        data = resp.json()
        assert data["first_name"] == "Combo"
        assert data["last_name"] == "User"
        assert data["phone"] == "+15550009999"


# ============================================================
# Issue 4 — Payment response uses full name over email
# ============================================================

class TestIssue4PaymentNameEnrichment:
    """sender_name / receiver_name in PaymentResponse should show 'First Last'
    when those fields are set on the consumer user, falling back to email."""

    @pytest.fixture(autouse=True)
    def _setup(self, db_session, seed_data):
        self._db = db_session

    def _add_consumer(self, uid, email, first=None, last=None,
                      balance="300.00"):
        u = User(
            id=uid, email=email,
            hashed_password=hash_password("pass"),
            role="user",
            first_name=first,
            last_name=last,
        )
        self._db.add(u)
        self._db.commit()
        wallet_credit(self._db, uid, Decimal(balance), description="seed")
        return create_access_token({"sub": uid, "email": email, "role": "user"})

    def _pay_and_fetch(self, client, token):
        resp = client.post("/consumer/pay", json={
            "merchant_id": "merchant-001",
            "amount": "10.00",
            "idempotency_key": str(uuid.uuid4()),
            "description": "name enrichment test",
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, resp.text
        txn_id = resp.json()["transaction_id"]
        get_resp = client.get(f"/payments/{txn_id}", headers=get_auth_header())
        assert get_resp.status_code == 200
        return get_resp.json()

    def test_full_name_shown_when_both_fields_set(self, client):
        tok = self._add_consumer("u-full", "full@test.com", "Raja", "Singh")
        data = self._pay_and_fetch(client, tok)
        assert data["sender_name"] == "Raja Singh"

    def test_first_name_only_when_no_last_name(self, client):
        tok = self._add_consumer("u-fn", "fn@test.com", first="Alice")
        data = self._pay_and_fetch(client, tok)
        assert data["sender_name"] == "Alice"

    def test_last_name_only_when_no_first_name(self, client):
        tok = self._add_consumer("u-ln", "ln@test.com", last="Smith")
        data = self._pay_and_fetch(client, tok)
        assert data["sender_name"] == "Smith"

    def test_falls_back_to_email_when_no_name(self, client):
        tok = self._add_consumer("u-email", "emailonly@test.com")
        data = self._pay_and_fetch(client, tok)
        assert data["sender_name"] == "emailonly@test.com"

    def test_receiver_name_still_shows_merchant_name(self, client):
        """Receiver is a merchant; receiver_name should still be the merchant name."""
        tok = self._add_consumer("u-recv", "recv@test.com", "Bob", "Jones")
        data = self._pay_and_fetch(client, tok)
        assert data["receiver_name"] == "Acme Corp"
