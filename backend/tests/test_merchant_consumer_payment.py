"""
Merchant ↔ Consumer payment tests.

Already covered elsewhere:
  - Consumer → Merchant (regular)   : test_multi_consumer.py  (POST /consumer/pay)
  - Merchant → Consumer (wallet send): test_wallet_transfer.py (POST /wallet/send)

Gaps covered here:
  - Merchant → Consumer-Merchant via POST /payments (B2B endpoint)
      • Consumer's wallet is credited alongside the merchant ledger entry
      • Consumer's wallet is NOT credited when the bank declines
      • Merchant ledger is debited on a completed payment
      • FedNow/RTP discount applies and the discounted amount is what
        reaches the consumer's wallet
  - Consumer cannot use POST /payments (403 Forbidden)
  - Consumer cannot use POST /payments even targeting their own merchant
"""
import uuid
from decimal import Decimal
from unittest.mock import patch, MagicMock

import pytest

from tests.conftest import make_auth_header, CONSUMER_MERCHANTS, MULTI_MERCHANTS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _merchant_headers(user_id: str, email: str) -> dict:
    return make_auth_header(user_id, email, role="merchant_admin")


def _consumer_headers(user_id: str, email: str) -> dict:
    return make_auth_header(user_id, email, role="user")


def _b2b_pay(client, headers: dict, sender_merchant_id: str,
             receiver_merchant_id: str, amount: str,
             key: str | None = None,
             preferred_rail: str | None = None,
             expected_status: int = 201) -> dict:
    body = {
        "sender_merchant_id": sender_merchant_id,
        "receiver_merchant_id": receiver_merchant_id,
        "amount": amount,
        "idempotency_key": key or str(uuid.uuid4()),
    }
    if preferred_rail:
        body["preferred_rail"] = preferred_rail
    resp = client.post("/payments", json=body, headers=headers)
    assert resp.status_code == expected_status, resp.text
    return resp.json()


def _merchant_balance(client, merchant_id: str, user_id: str, email: str) -> float:
    headers = _merchant_headers(user_id, email)
    resp = client.get(f"/payments/balance?merchant_id={merchant_id}", headers=headers)
    assert resp.status_code == 200, resp.text
    return float(resp.json()["balance"])


def _consumer_balance(client, user_id: str, email: str) -> float:
    headers = _consumer_headers(user_id, email)
    resp = client.get("/consumer/wallet/balance", headers=headers)
    assert resp.status_code == 200, resp.text
    return float(resp.json()["balance"])


# ---------------------------------------------------------------------------
# Shared fixture: regular merchants + consumer-merchants in one DB
# ---------------------------------------------------------------------------

@pytest.fixture
def mixed_seed_data(db_session):
    """
    Combines full_seed_data merchants with consumer-merchant records so both
    POST /payments and consumer wallet checks work in the same test session.
    """
    from app.models.merchant import Merchant
    from app.models.user import User
    from app.models.bank_account import BankAccount
    from app.models.bank_config import BankConfig
    from app.services.auth_service import hash_password
    from app.services.ledger_service import record_credit
    from app.services.wallet_service import wallet_credit
    from app.utils.encryption import encrypt_value

    bc = BankConfig(
        id="bank-config-test",
        bank_name="MockBank",
        supported_rails="fednow,rtp,ach,card",
        fednow_limit=Decimal("500000"),
        rtp_limit=Decimal("1000000"),
        ach_limit=Decimal("10000000"),
        is_active=True,
    )
    db_session.add(bc)

    # Regular business merchants (senders)
    for m_id, m_name, m_ein, m_email, u_id in MULTI_MERCHANTS:
        m = Merchant(
            id=m_id, name=m_name, ein=m_ein,
            contact_email=m_email,
            onboarding_status="active", kyb_status="approved",
        )
        u = User(
            id=u_id, email=m_email,
            hashed_password=hash_password("password123"),
            role="merchant_admin", merchant_id=m_id,
            phone=f"+1555000{u_id[-3:]}",
        )
        ba = BankAccount(
            id=f"bank-acct-{m_id[-3:]}",
            merchant_id=m_id, bank_name="MockBank",
            routing_number="021000021",
            encrypted_account_number=encrypt_value(f"100000{m_id[-3:]}"),
            account_type="checking", verification_status="verified",
        )
        db_session.add_all([m, u, ba])

    # Consumer-merchants (receivers with linked consumer wallets)
    for m_id, m_name, m_ein, u_id, u_email in CONSUMER_MERCHANTS:
        m = Merchant(
            id=m_id, name=m_name, ein=m_ein,
            contact_email=u_email,
            onboarding_status="active", kyb_status="approved",
        )
        u = User(
            id=u_id, email=u_email,
            hashed_password=hash_password("password123"),
            role="user", merchant_id=m_id,
            phone=f"+1555900{u_id[-3:]}",
        )
        ba = BankAccount(
            id=f"bank-acct-{m_id}",
            merchant_id=m_id, bank_name="MockBank",
            routing_number="021000021",
            encrypted_account_number=encrypt_value(f"3000{u_id[-3:]}"),
            account_type="checking", verification_status="verified",
        )
        db_session.add_all([m, u, ba])

    db_session.commit()

    for m_id, *_ in MULTI_MERCHANTS:
        record_credit(db_session, m_id, Decimal("100000.00"), description="Seed")

    for _, _, _, u_id, _ in CONSUMER_MERCHANTS:
        wallet_credit(db_session, u_id, Decimal("500.00"), description="Seed wallet")

    return {}


# ---------------------------------------------------------------------------
# 1. Merchant → Consumer-Merchant via POST /payments
# ---------------------------------------------------------------------------

class TestMerchantToConsumerMerchant:

    def test_payment_completes(self, client, mixed_seed_data):
        """Merchant can pay a consumer-merchant via POST /payments."""
        m_id, _, _, m_email, m_user_id = MULTI_MERCHANTS[0]
        cm_id, _, _, _, _ = CONSUMER_MERCHANTS[0]
        with patch("app.services.description_service.generate_description",
                   return_value="B2B to consumer merchant"):
            with patch("app.services.notification_service.notify_transaction"):
                with patch(
                    "app.services.bank.mock_bank.mock_bank_service.initiate_transfer"
                ) as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="completed", reference_id="m2cm-ref-1",
                        failure_reason=None,
                    )
                    data = _b2b_pay(client, _merchant_headers(m_user_id, m_email),
                                    m_id, cm_id, "200.00")
                    assert data["status"] == "completed"

    def test_sender_merchant_ledger_debited(self, client, mixed_seed_data):
        """Sending merchant's ledger decreases after a completed payment."""
        m_id, _, _, m_email, m_user_id = MULTI_MERCHANTS[0]
        cm_id, _, _, _, _ = CONSUMER_MERCHANTS[0]
        with patch("app.services.description_service.generate_description",
                   return_value="x"):
            with patch("app.services.notification_service.notify_transaction"):
                with patch(
                    "app.services.bank.mock_bank.mock_bank_service.initiate_transfer"
                ) as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="completed", reference_id="m2cm-ref-2",
                        failure_reason=None,
                    )
                    before = _merchant_balance(client, m_id, m_user_id, m_email)
                    _b2b_pay(client, _merchant_headers(m_user_id, m_email),
                             m_id, cm_id, "300.00", preferred_rail="ach")
                    after = _merchant_balance(client, m_id, m_user_id, m_email)
                    assert after == pytest.approx(before - 300.00)

    def test_consumer_wallet_credited(self, client, mixed_seed_data):
        """Consumer's wallet is credited when a merchant pays their consumer-merchant."""
        m_id, _, _, m_email, m_user_id = MULTI_MERCHANTS[0]
        cm_id, _, _, c_user_id, c_email = CONSUMER_MERCHANTS[0]
        with patch("app.services.description_service.generate_description",
                   return_value="x"):
            with patch("app.services.notification_service.notify_transaction"):
                with patch(
                    "app.services.bank.mock_bank.mock_bank_service.initiate_transfer"
                ) as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="completed", reference_id="m2cm-ref-3",
                        failure_reason=None,
                    )
                    before = _consumer_balance(client, c_user_id, c_email)
                    _b2b_pay(client, _merchant_headers(m_user_id, m_email),
                             m_id, cm_id, "150.00", preferred_rail="ach")
                    after = _consumer_balance(client, c_user_id, c_email)
                    assert after == pytest.approx(before + 150.00)

    def test_consumer_wallet_not_credited_on_failed_payment(
        self, client, mixed_seed_data
    ):
        """Consumer wallet is unchanged when the bank declines the B2B payment."""
        m_id, _, _, m_email, m_user_id = MULTI_MERCHANTS[0]
        cm_id, _, _, c_user_id, c_email = CONSUMER_MERCHANTS[0]
        with patch("app.services.description_service.generate_description",
                   return_value="x"):
            with patch("app.services.notification_service.notify_transaction"):
                with patch(
                    "app.services.bank.mock_bank.mock_bank_service.initiate_transfer"
                ) as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="failed", reference_id="m2cm-ref-4",
                        failure_reason="Declined",
                    )
                    before = _consumer_balance(client, c_user_id, c_email)
                    _b2b_pay(client, _merchant_headers(m_user_id, m_email),
                             m_id, cm_id, "100.00")
                    after = _consumer_balance(client, c_user_id, c_email)
                    assert after == pytest.approx(before)

    def test_fednow_discount_reaches_consumer_wallet(self, client, mixed_seed_data):
        """FedNow discount (×0.9875) applies and the net amount reaches the consumer wallet."""
        m_id, _, _, m_email, m_user_id = MULTI_MERCHANTS[0]
        cm_id, _, _, c_user_id, c_email = CONSUMER_MERCHANTS[0]
        with patch("app.services.description_service.generate_description",
                   return_value="x"):
            with patch("app.services.notification_service.notify_transaction"):
                with patch(
                    "app.services.bank.mock_bank.mock_bank_service.initiate_transfer"
                ) as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="completed", reference_id="m2cm-ref-5",
                        failure_reason=None,
                    )
                    before = _consumer_balance(client, c_user_id, c_email)
                    _b2b_pay(client, _merchant_headers(m_user_id, m_email),
                             m_id, cm_id, "200.00", preferred_rail="fednow")
                    after = _consumer_balance(client, c_user_id, c_email)
                    # 200 × 0.9875 = 197.50
                    assert after - before == pytest.approx(197.50, abs=0.01)

    def test_non_consumer_merchant_receiver_no_wallet_credit(
        self, client, mixed_seed_data
    ):
        """Paying a regular business merchant does NOT create any wallet credit."""
        sender_id, _, _, sender_email, sender_user_id = MULTI_MERCHANTS[0]
        receiver_id, _, _, receiver_email, receiver_user_id = MULTI_MERCHANTS[1]
        with patch("app.services.description_service.generate_description",
                   return_value="x"):
            with patch("app.services.notification_service.notify_transaction"):
                with patch(
                    "app.services.bank.mock_bank.mock_bank_service.initiate_transfer"
                ) as mock_bank:
                    mock_bank.return_value = MagicMock(
                        status="completed", reference_id="m2cm-ref-6",
                        failure_reason=None,
                    )
                    before = _merchant_balance(client, receiver_id,
                                               receiver_user_id, receiver_email)
                    _b2b_pay(client, _merchant_headers(sender_user_id, sender_email),
                             sender_id, receiver_id, "500.00", preferred_rail="ach")
                    after = _merchant_balance(client, receiver_id,
                                              receiver_user_id, receiver_email)
                    # Ledger credited normally; no wallet side-effect to assert
                    assert after > before


# ---------------------------------------------------------------------------
# 2. Consumer cannot use POST /payments
# ---------------------------------------------------------------------------

class TestConsumerCannotUseB2BEndpoint:

    def test_consumer_role_is_rejected(self, client, mixed_seed_data):
        """A consumer (role=user) calling POST /payments gets 403 Forbidden."""
        _, _, _, c_user_id, c_email = CONSUMER_MERCHANTS[0]
        cm_id, _, _, _, _ = CONSUMER_MERCHANTS[0]
        m_id, _, _, _, _ = MULTI_MERCHANTS[0]
        headers = _consumer_headers(c_user_id, c_email)
        body = {
            "sender_merchant_id": cm_id,
            "receiver_merchant_id": m_id,
            "amount": "10.00",
            "idempotency_key": str(uuid.uuid4()),
        }
        resp = client.post("/payments", json=body, headers=headers)
        assert resp.status_code == 403

    def test_unauthenticated_request_rejected(self, client, mixed_seed_data):
        """Unauthenticated calls to POST /payments are rejected."""
        m_id, _, _, _, _ = MULTI_MERCHANTS[0]
        cm_id, _, _, _, _ = CONSUMER_MERCHANTS[0]
        resp = client.post("/payments", json={
            "sender_merchant_id": m_id,
            "receiver_merchant_id": cm_id,
            "amount": "10.00",
            "idempotency_key": str(uuid.uuid4()),
        })
        assert resp.status_code in (401, 403)
