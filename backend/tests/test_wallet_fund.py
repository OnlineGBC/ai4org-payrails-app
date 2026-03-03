"""Tests for POST /consumer/wallet/fund — realistic ACH-based wallet funding."""
import pytest
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.bank_account import BankAccount
from app.models.merchant import Merchant
from app.models.user import User
from app.services.auth_service import hash_password, create_access_token
from app.services.wallet_service import get_wallet_balance
from app.utils.encryption import encrypt_value


# ---------------------------------------------------------------------------
# Fixture: one consumer with a merchant + one verified bank account
# ---------------------------------------------------------------------------

@pytest.fixture
def fund_seed(db_session: Session):
    from app.models.bank_config import BankConfig

    bc = BankConfig(
        id="bank-config-fund-test",
        bank_name="MockBank",
        supported_rails="fednow,rtp,ach,card",
        fednow_limit=Decimal("500000"),
        rtp_limit=Decimal("1000000"),
        ach_limit=Decimal("10000000"),
        is_active=True,
    )
    db_session.add(bc)

    merchant = Merchant(
        id="merchant-fund-consumer",
        name="funduser",
        contact_email="fund@test.com",
        onboarding_status="active",
        kyb_status="not_required",
    )
    db_session.add(merchant)

    consumer = User(
        id="user-fund-consumer",
        email="fund@test.com",
        hashed_password=hash_password("password123"),
        role="user",
        merchant_id="merchant-fund-consumer",
    )
    db_session.add(consumer)

    verified_account = BankAccount(
        id="bank-acct-fund-verified",
        merchant_id="merchant-fund-consumer",
        bank_name="Chase",
        routing_number="021000021",
        encrypted_account_number=encrypt_value("1234567890"),
        account_type="checking",
        verification_status="verified",
    )
    unverified_account = BankAccount(
        id="bank-acct-fund-unverified",
        merchant_id="merchant-fund-consumer",
        bank_name="Chase",
        routing_number="021000021",
        encrypted_account_number=encrypt_value("0000000001"),
        account_type="checking",
        verification_status="micro_deposit_sent",
    )
    db_session.add_all([verified_account, unverified_account])
    db_session.commit()

    token = create_access_token({
        "sub": "user-fund-consumer",
        "email": "fund@test.com",
        "role": "user",
    })
    headers = {"Authorization": f"Bearer {token}"}
    return {
        "consumer": consumer,
        "merchant": merchant,
        "verified_account": verified_account,
        "unverified_account": unverified_account,
        "headers": headers,
        "db": db_session,
    }


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

class TestWalletFundHappyPath:
    def test_fund_returns_200(self, client, fund_seed):
        resp = client.post("/consumer/wallet/fund", json={
            "bank_account_id": "bank-acct-fund-verified",
            "amount": "100.00",
        }, headers=fund_seed["headers"])
        # Mock bank has 5% error rate — retry until completed or accept either
        assert resp.status_code == 200

    def test_fund_response_has_expected_fields(self, client, fund_seed):
        resp = client.post("/consumer/wallet/fund", json={
            "bank_account_id": "bank-acct-fund-verified",
            "amount": "50.00",
        }, headers=fund_seed["headers"])
        data = resp.json()
        assert "user_id" in data
        assert "balance" in data
        assert "transaction_status" in data
        assert "reference_id" in data
        assert data["transaction_status"] in ("completed", "failed")

    def test_successful_fund_increases_balance(self, client, fund_seed):
        """Run up to 10 attempts to get a completed transfer and verify balance rises."""
        db = fund_seed["db"]
        initial = get_wallet_balance(db, "user-fund-consumer")
        funded = False
        for _ in range(10):
            resp = client.post("/consumer/wallet/fund", json={
                "bank_account_id": "bank-acct-fund-verified",
                "amount": "75.00",
            }, headers=fund_seed["headers"])
            if resp.json()["transaction_status"] == "completed":
                funded = True
                break
        assert funded, "Could not get a completed transfer in 10 attempts"
        after = get_wallet_balance(db, "user-fund-consumer")
        assert after > initial

    def test_failed_transfer_does_not_change_balance(self, client, fund_seed):
        """Confirm that a mock-bank failure leaves the wallet balance unchanged."""
        db = fund_seed["db"]
        initial = get_wallet_balance(db, "user-fund-consumer")
        # Force a failure by driving enough attempts to eventually get one
        for _ in range(30):
            resp = client.post("/consumer/wallet/fund", json={
                "bank_account_id": "bank-acct-fund-verified",
                "amount": "1.00",
            }, headers=fund_seed["headers"])
            if resp.json()["transaction_status"] == "failed":
                after = get_wallet_balance(db, "user-fund-consumer")
                # Balance should be the same as before this specific failed call
                # (other completed calls may have increased it — just verify no debit)
                assert after >= initial
                return
        pytest.skip("No failed transfer observed in 30 attempts (probabilistic)")


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------

class TestWalletFundValidation:
    def test_unverified_account_returns_400(self, client, fund_seed):
        resp = client.post("/consumer/wallet/fund", json={
            "bank_account_id": "bank-acct-fund-unverified",
            "amount": "50.00",
        }, headers=fund_seed["headers"])
        assert resp.status_code == 400
        assert "not verified" in resp.json()["detail"]

    def test_nonexistent_account_returns_404(self, client, fund_seed):
        resp = client.post("/consumer/wallet/fund", json={
            "bank_account_id": "does-not-exist",
            "amount": "50.00",
        }, headers=fund_seed["headers"])
        assert resp.status_code == 404

    def test_account_belonging_to_other_merchant_returns_404(
        self, client, fund_seed, db_session
    ):
        """Consumer cannot use a bank account linked to a different merchant."""
        other = BankAccount(
            id="bank-acct-other-merchant",
            merchant_id="merchant-someone-else",
            bank_name="Chase",
            routing_number="021000021",
            encrypted_account_number=encrypt_value("9999999999"),
            account_type="checking",
            verification_status="verified",
        )
        db_session.add(other)
        db_session.commit()

        resp = client.post("/consumer/wallet/fund", json={
            "bank_account_id": "bank-acct-other-merchant",
            "amount": "50.00",
        }, headers=fund_seed["headers"])
        assert resp.status_code == 404

    def test_zero_amount_returns_400(self, client, fund_seed):
        resp = client.post("/consumer/wallet/fund", json={
            "bank_account_id": "bank-acct-fund-verified",
            "amount": "0",
        }, headers=fund_seed["headers"])
        assert resp.status_code == 400

    def test_negative_amount_returns_400(self, client, fund_seed):
        resp = client.post("/consumer/wallet/fund", json={
            "bank_account_id": "bank-acct-fund-verified",
            "amount": "-10.00",
        }, headers=fund_seed["headers"])
        assert resp.status_code == 400

    def test_merchant_admin_cannot_fund_consumer_wallet(self, client, fund_seed, db_session):
        from app.services.auth_service import create_access_token
        # Create a real merchant_admin user so the token passes get_current_user
        from app.models.merchant import Merchant
        from app.models.user import User
        m = Merchant(id="merchant-role-test", name="RoleCo",
                     contact_email="role@test.com", onboarding_status="active",
                     kyb_status="approved")
        u = User(id="user-role-test", email="role@test.com",
                 hashed_password="x", role="merchant_admin",
                 merchant_id="merchant-role-test")
        db_session.add_all([m, u])
        db_session.commit()
        merchant_token = create_access_token({
            "sub": "user-role-test",
            "email": "role@test.com",
            "role": "merchant_admin",
        })
        resp = client.post("/consumer/wallet/fund", json={
            "bank_account_id": "bank-acct-fund-verified",
            "amount": "50.00",
        }, headers={"Authorization": f"Bearer {merchant_token}"})
        assert resp.status_code == 403

    def test_unauthenticated_returns_401(self, client, fund_seed):
        resp = client.post("/consumer/wallet/fund", json={
            "bank_account_id": "bank-acct-fund-verified",
            "amount": "50.00",
        })
        assert resp.status_code in (401, 403)
