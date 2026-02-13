import uuid
from decimal import Decimal

from app.services.bank.mock_bank import MockBankService, RAIL_LIMITS
from app.services.bank.schemas import TransferRequest


def test_fednow_within_limit():
    bank = MockBankService()
    req = TransferRequest(
        sender_account_id="s1", receiver_account_id="r1",
        amount=Decimal("1000"), rail="fednow", idempotency_key=str(uuid.uuid4()),
    )
    resp = bank.initiate_transfer(req)
    assert resp.status in ("completed", "failed")
    assert resp.rail == "fednow"


def test_fednow_exceeds_limit():
    bank = MockBankService()
    req = TransferRequest(
        sender_account_id="s1", receiver_account_id="r1",
        amount=Decimal("600000"), rail="fednow", idempotency_key=str(uuid.uuid4()),
    )
    resp = bank.initiate_transfer(req)
    assert resp.status == "failed"
    assert "limit" in resp.failure_reason.lower()


def test_rtp_within_limit():
    bank = MockBankService()
    req = TransferRequest(
        sender_account_id="s1", receiver_account_id="r1",
        amount=Decimal("750000"), rail="rtp", idempotency_key=str(uuid.uuid4()),
    )
    resp = bank.initiate_transfer(req)
    assert resp.status in ("completed", "failed")


def test_idempotency():
    bank = MockBankService()
    key = str(uuid.uuid4())
    req = TransferRequest(
        sender_account_id="s1", receiver_account_id="r1",
        amount=Decimal("100"), rail="fednow", idempotency_key=key,
    )
    resp1 = bank.initiate_transfer(req)
    resp2 = bank.initiate_transfer(req)
    assert resp1.reference_id == resp2.reference_id


def test_get_transfer_status():
    bank = MockBankService()
    req = TransferRequest(
        sender_account_id="s1", receiver_account_id="r1",
        amount=Decimal("50"), rail="ach", idempotency_key=str(uuid.uuid4()),
    )
    resp = bank.initiate_transfer(req)
    status_resp = bank.get_transfer_status(resp.reference_id)
    assert status_resp.reference_id == resp.reference_id


def test_get_transfer_status_not_found():
    bank = MockBankService()
    resp = bank.get_transfer_status("nonexistent")
    assert resp.status == "not_found"


def test_get_balance():
    bank = MockBankService()
    resp = bank.get_balance("any-account")
    assert resp.available_balance == Decimal("100000.00")


def test_rail_limits_defined():
    assert RAIL_LIMITS["fednow"] == Decimal("500000")
    assert RAIL_LIMITS["rtp"] == Decimal("1000000")
    assert RAIL_LIMITS["ach"] == Decimal("10000000")
    assert RAIL_LIMITS["card"] == Decimal("50000")
