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


def test_payment_no_auth(client):
    resp = client.post("/payments", json={
        "sender_merchant_id": "merchant-001",
        "receiver_merchant_id": "merchant-002",
        "amount": "100.00",
        "idempotency_key": str(uuid.uuid4()),
    })
    assert resp.status_code in (401, 403)
