import uuid
from tests.conftest import get_auth_header


def test_create_payment(client, seed_data):
    headers = get_auth_header()
    resp = client.post("/payments", json={
        "sender_merchant_id": "merchant-001",
        "receiver_merchant_id": "merchant-002",
        "amount": "1000.00",
        "idempotency_key": str(uuid.uuid4()),
    }, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] in ("completed", "failed")
    assert data["rail"] == "fednow"


def test_idempotency(client, seed_data):
    headers = get_auth_header()
    key = str(uuid.uuid4())
    resp1 = client.post("/payments", json={
        "sender_merchant_id": "merchant-001",
        "receiver_merchant_id": "merchant-002",
        "amount": "500.00",
        "idempotency_key": key,
    }, headers=headers)
    resp2 = client.post("/payments", json={
        "sender_merchant_id": "merchant-001",
        "receiver_merchant_id": "merchant-002",
        "amount": "500.00",
        "idempotency_key": key,
    }, headers=headers)
    assert resp1.json()["id"] == resp2.json()["id"]


def test_get_payment(client, seed_data):
    headers = get_auth_header()
    create_resp = client.post("/payments", json={
        "sender_merchant_id": "merchant-001",
        "receiver_merchant_id": "merchant-002",
        "amount": "100.00",
        "idempotency_key": str(uuid.uuid4()),
    }, headers=headers)
    pid = create_resp.json()["id"]
    resp = client.get(f"/payments/{pid}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == pid


def test_list_payments(client, seed_data):
    headers = get_auth_header()
    for _ in range(3):
        client.post("/payments", json={
            "sender_merchant_id": "merchant-001",
            "receiver_merchant_id": "merchant-002",
            "amount": "50.00",
            "idempotency_key": str(uuid.uuid4()),
        }, headers=headers)
    resp = client.get("/payments", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] >= 3


def test_filter_by_status(client, seed_data, db_session):
    """Filter by status returns only matching transactions."""
    from app.models.transaction import Transaction
    headers = get_auth_header()
    # Create a payment and force it to 'completed'
    resp = client.post("/payments", json={
        "sender_merchant_id": "merchant-001",
        "receiver_merchant_id": "merchant-002",
        "amount": "11.00",
        "idempotency_key": str(uuid.uuid4()),
    }, headers=headers)
    pid = resp.json()["id"]
    txn = db_session.query(Transaction).filter(Transaction.id == pid).first()
    txn.status = "completed"
    db_session.commit()

    completed = client.get("/payments?status=completed", headers=headers)
    assert completed.status_code == 200
    statuses = [t["status"] for t in completed.json()["items"]]
    assert all(s == "completed" for s in statuses)
    assert any(t["id"] == pid for t in completed.json()["items"])

    cancelled = client.get("/payments?status=cancelled", headers=headers)
    assert cancelled.status_code == 200
    assert all(t["id"] != pid for t in cancelled.json()["items"])


def test_filter_by_rail(client, seed_data):
    """Filter by rail returns only transactions on that rail."""
    headers = get_auth_header()
    client.post("/payments", json={
        "sender_merchant_id": "merchant-001",
        "receiver_merchant_id": "merchant-002",
        "amount": "12.00",
        "idempotency_key": str(uuid.uuid4()),
    }, headers=headers)
    resp = client.get("/payments?rail=fednow", headers=headers)
    assert resp.status_code == 200
    for txn in resp.json()["items"]:
        assert txn["rail"] == "fednow"


def test_filter_combined_status_and_rail(client, seed_data, db_session):
    """Combined status+rail filter narrows results to both criteria."""
    from app.models.transaction import Transaction
    headers = get_auth_header()
    resp = client.post("/payments", json={
        "sender_merchant_id": "merchant-001",
        "receiver_merchant_id": "merchant-002",
        "amount": "13.00",
        "idempotency_key": str(uuid.uuid4()),
    }, headers=headers)
    pid = resp.json()["id"]
    txn = db_session.query(Transaction).filter(Transaction.id == pid).first()
    txn.status = "failed"
    db_session.commit()

    result = client.get("/payments?status=failed&rail=fednow", headers=headers)
    assert result.status_code == 200
    for t in result.json()["items"]:
        assert t["status"] == "failed"
        assert t["rail"] == "fednow"


def test_balance(client, seed_data):
    headers = get_auth_header()
    resp = client.get("/payments/balance?merchant_id=merchant-001", headers=headers)
    assert resp.status_code == 200
    assert float(resp.json()["balance"]) == 100000.00


def test_cancel_payment(client, seed_data):
    headers = get_auth_header()
    # We need a payment in pending/processing state — create and try to cancel
    # Note: mock bank completes instantly, so this may fail on "completed" status
    create_resp = client.post("/payments", json={
        "sender_merchant_id": "merchant-001",
        "receiver_merchant_id": "merchant-002",
        "amount": "25.00",
        "idempotency_key": str(uuid.uuid4()),
    }, headers=headers)
    pid = create_resp.json()["id"]
    status = create_resp.json()["status"]
    resp = client.post(f"/payments/{pid}/cancel", headers=headers)
    if status in ("completed", "failed"):
        assert resp.status_code == 400
    else:
        assert resp.status_code == 200


def test_cancel_completed_payment_returns_400(client, seed_data, db_session):
    """A completed payment cannot be cancelled — backend raises 400."""
    from app.models.transaction import Transaction
    headers = get_auth_header()
    create_resp = client.post("/payments", json={
        "sender_merchant_id": "merchant-001",
        "receiver_merchant_id": "merchant-002",
        "amount": "30.00",
        "idempotency_key": str(uuid.uuid4()),
    }, headers=headers)
    pid = create_resp.json()["id"]
    # Force status to 'completed' so cancel should be rejected
    txn = db_session.query(Transaction).filter(Transaction.id == pid).first()
    txn.status = "completed"
    db_session.commit()
    resp = client.post(f"/payments/{pid}/cancel", headers=headers)
    assert resp.status_code == 400
    assert "cannot cancel" in resp.json()["detail"].lower()


def test_cancel_pending_payment_succeeds(client, seed_data, db_session):
    """Forcing a payment to 'pending' and then cancelling succeeds."""
    from app.models.transaction import Transaction
    headers = get_auth_header()
    create_resp = client.post("/payments", json={
        "sender_merchant_id": "merchant-001",
        "receiver_merchant_id": "merchant-002",
        "amount": "40.00",
        "idempotency_key": str(uuid.uuid4()),
    }, headers=headers)
    pid = create_resp.json()["id"]
    txn = db_session.query(Transaction).filter(Transaction.id == pid).first()
    txn.status = "pending"
    db_session.commit()
    resp = client.post(f"/payments/{pid}/cancel", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


def test_cancel_nonexistent_payment_returns_400(client, seed_data):
    headers = get_auth_header()
    resp = client.post("/payments/does-not-exist/cancel", headers=headers)
    assert resp.status_code == 400


def test_payment_no_auth(client):
    resp = client.post("/payments", json={
        "sender_merchant_id": "merchant-001",
        "receiver_merchant_id": "merchant-002",
        "amount": "100.00",
        "idempotency_key": str(uuid.uuid4()),
    })
    assert resp.status_code in (401, 403)
