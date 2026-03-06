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


def test_submit_kyb_with_optional_fields(client, seed_data):
    headers = get_auth_header()
    create_resp = client.post("/merchants", json={
        "name": "FullKYBCo",
        "contact_email": "fullkyb@co.com",
    }, headers=headers)
    mid = create_resp.json()["id"]
    resp = client.post(f"/merchants/{mid}/kyb", json={
        "ein": "99-8887776",
        "business_name": "FullKYBCo",
        "business_address": "123 Main St, NY",
        "representative_name": "Jane Doe",
        "representative_ssn_last4": "5678",
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["kyb_status"] == "approved"
    assert resp.json()["ein"] == "99-8887776"


def test_submit_kyb_missing_required_fields(client, seed_data):
    headers = get_auth_header()
    create_resp = client.post("/merchants", json={
        "name": "NoEINCo",
        "contact_email": "noein@co.com",
    }, headers=headers)
    mid = create_resp.json()["id"]
    # Missing 'ein' — should fail Pydantic validation
    resp = client.post(f"/merchants/{mid}/kyb", json={
        "business_name": "NoEINCo",
    }, headers=headers)
    assert resp.status_code == 422


def test_submit_kyb_nonexistent_merchant(client, seed_data):
    headers = get_auth_header()
    resp = client.post("/merchants/does-not-exist/kyb", json={
        "ein": "11-2223334",
        "business_name": "Ghost Co",
    }, headers=headers)
    assert resp.status_code == 400
    assert "not found" in resp.json()["detail"].lower()


def test_add_bank_account(client, seed_data):
    headers = get_auth_header()
    resp = client.post("/merchants/merchant-001/bank-accounts", json={
        "bank_name": "JPMorganTest",
        "routing_number": "021000021",
        "account_number": "9876543210",
    }, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["verification_status"] == "micro_deposit_sent"
    assert resp.json()["account_number_last4"] == "3210"
    assert resp.json()["bank_name"] == "JPMorganTest"


def test_add_bank_account_missing_bank_name(client, seed_data):
    """bank_name is now required — omitting it returns 422."""
    headers = get_auth_header()
    resp = client.post("/merchants/merchant-001/bank-accounts", json={
        "routing_number": "021000021",
        "account_number": "9876543210",
    }, headers=headers)
    assert resp.status_code == 422


def test_add_bank_account_invalid_routing(client, seed_data):
    headers = get_auth_header()
    resp = client.post("/merchants/merchant-001/bank-accounts", json={
        "bank_name": "TestBank",
        "routing_number": "123456789",
        "account_number": "9876543210",
    }, headers=headers)
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Invalid routing number"


def test_add_bank_account_bad_checksum_routing(client, seed_data):
    """Routing number 061000027 fails ABA checksum — must return 400 with clear message."""
    headers = get_auth_header()
    resp = client.post("/merchants/merchant-001/bank-accounts", json={
        "bank_name": "TestBank",
        "routing_number": "061000027",
        "account_number": "9876543210",
    }, headers=headers)
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Invalid routing number"


# ---------------------------------------------------------------------------
# GET /banks — public endpoint
# ---------------------------------------------------------------------------

def test_list_banks_no_auth(client, seed_data):
    """GET /banks requires no authentication."""
    resp = client.get("/banks")
    assert resp.status_code == 200
    banks = resp.json()
    assert isinstance(banks, list)
    assert len(banks) > 0


def test_list_banks_structure(client, seed_data):
    """Each bank entry has id, bank_name, and supported_rails list."""
    resp = client.get("/banks")
    assert resp.status_code == 200
    for bank in resp.json():
        assert "id" in bank
        assert "bank_name" in bank
        assert isinstance(bank["supported_rails"], list)


def test_list_banks_sorted(client, seed_data):
    """Banks are returned in alphabetical order."""
    resp = client.get("/banks")
    names = [b["bank_name"] for b in resp.json()]
    assert names == sorted(names)


def test_list_banks_contains_expected(client, seed_data):
    """MockBank is always seeded by the startup fixture."""
    resp = client.get("/banks")
    names = [b["bank_name"] for b in resp.json()]
    assert "MockBank" in names


def test_verify_micro_deposits(client, seed_data):
    headers = get_auth_header()
    create_resp = client.post("/merchants/merchant-001/bank-accounts", json={
        "bank_name": "TestBank",
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
        "bank_name": "TestBank",
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
