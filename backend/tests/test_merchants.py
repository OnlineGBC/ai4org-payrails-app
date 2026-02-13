from tests.conftest import get_auth_header


def test_create_merchant(client, seed_data):
    headers = get_auth_header()
    resp = client.post("/merchants", json={
        "name": "TestCo",
        "contact_email": "test@co.com",
    }, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["name"] == "TestCo"
    assert resp.json()["onboarding_status"] == "pending"


def test_get_merchant_status(client, seed_data):
    headers = get_auth_header()
    resp = client.get("/merchants/merchant-001/status", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["kyb_status"] == "approved"


def test_update_merchant(client, seed_data):
    headers = get_auth_header()
    resp = client.put("/merchants/merchant-001", json={
        "contact_phone": "555-0100",
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["contact_phone"] == "555-0100"


def test_submit_kyb(client, seed_data):
    headers = get_auth_header()
    create_resp = client.post("/merchants", json={
        "name": "KYBTestCo",
        "contact_email": "kyb@co.com",
    }, headers=headers)
    mid = create_resp.json()["id"]
    resp = client.post(f"/merchants/{mid}/kyb", json={
        "ein": "11-2223334",
        "business_name": "KYBTestCo",
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["kyb_status"] == "approved"
    assert resp.json()["onboarding_status"] == "active"


def test_add_bank_account(client, seed_data):
    headers = get_auth_header()
    resp = client.post("/merchants/merchant-001/bank-accounts", json={
        "routing_number": "021000021",
        "account_number": "9876543210",
    }, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["verification_status"] == "micro_deposit_sent"
    assert resp.json()["account_number_last4"] == "3210"


def test_add_bank_account_invalid_routing(client, seed_data):
    headers = get_auth_header()
    resp = client.post("/merchants/merchant-001/bank-accounts", json={
        "routing_number": "123456789",
        "account_number": "9876543210",
    }, headers=headers)
    assert resp.status_code == 400


def test_verify_micro_deposits(client, seed_data):
    headers = get_auth_header()
    create_resp = client.post("/merchants/merchant-001/bank-accounts", json={
        "routing_number": "021000021",
        "account_number": "1111222233",
    }, headers=headers)
    acct_id = create_resp.json()["id"]

    # Try wrong amounts — expect failure
    resp = client.post(
        f"/merchants/merchant-001/bank-accounts/{acct_id}/verify-micro-deposits",
        json={"amount_1": "0.00", "amount_2": "0.00"},
        headers=headers,
    )
    assert resp.status_code == 400


def test_instant_verify(client, seed_data):
    headers = get_auth_header()
    create_resp = client.post("/merchants/merchant-001/bank-accounts", json={
        "routing_number": "021000021",
        "account_number": "5555666677",
    }, headers=headers)
    acct_id = create_resp.json()["id"]
    resp = client.post(
        f"/merchants/merchant-001/bank-accounts/{acct_id}/verify-instant",
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["verification_status"] == "verified"
