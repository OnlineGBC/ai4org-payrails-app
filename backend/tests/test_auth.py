from tests.conftest import get_auth_header


def test_register(client):
    resp = client.post("/auth/register", json={
        "email": "new@test.com",
        "password": "secret123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@test.com"
    assert data["role"] == "user"
    # Consumer registration now creates a linked merchant
    assert data["merchant_id"] is not None


def test_register_duplicate(client):
    client.post("/auth/register", json={"email": "dup@test.com", "password": "secret123"})
    resp = client.post("/auth/register", json={"email": "dup@test.com", "password": "secret123"})
    assert resp.status_code == 409


def test_login(client):
    client.post("/auth/register", json={"email": "login@test.com", "password": "secret123"})
    resp = client.post("/auth/login", json={"email": "login@test.com", "password": "secret123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_wrong_password(client):
    client.post("/auth/register", json={"email": "wp@test.com", "password": "secret123"})
    resp = client.post("/auth/login", json={"email": "wp@test.com", "password": "wrong"})
    assert resp.status_code == 401


def test_me(client):
    client.post("/auth/register", json={"email": "me@test.com", "password": "secret123"})
    login_resp = client.post("/auth/login", json={"email": "me@test.com", "password": "secret123"})
    token = login_resp.json()["access_token"]
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@test.com"


def test_me_no_token(client):
    resp = client.get("/auth/me")
    assert resp.status_code in (401, 403)


def test_refresh(client):
    client.post("/auth/register", json={"email": "ref@test.com", "password": "secret123"})
    login_resp = client.post("/auth/login", json={"email": "ref@test.com", "password": "secret123"})
    refresh_token = login_resp.json()["refresh_token"]
    resp = client.post(f"/auth/refresh?refresh_token={refresh_token}")
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_register_merchant(client):
    resp = client.post("/auth/register/merchant", json={
        "email": "biz@test.com",
        "password": "secret123",
        "business_name": "Acme Corp",
        "ein": "12-3456789",
        "contact_email": "contact@acme.com",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "biz@test.com"
    assert data["role"] == "merchant_admin"
    assert data["merchant_id"] is not None


def test_register_merchant_duplicate_email(client):
    payload = {
        "email": "biz2@test.com",
        "password": "secret123",
        "business_name": "Acme2",
        "ein": "99-1111111",
        "contact_email": "biz2@test.com",
    }
    client.post("/auth/register/merchant", json=payload)
    resp = client.post("/auth/register/merchant", json={**payload, "ein": "99-2222222"})
    assert resp.status_code == 409


def test_register_merchant_duplicate_ein(client):
    client.post("/auth/register/merchant", json={
        "email": "biz3@test.com",
        "password": "secret123",
        "business_name": "Acme3",
        "ein": "77-9999999",
        "contact_email": "biz3@test.com",
    })
    resp = client.post("/auth/register/merchant", json={
        "email": "biz4@test.com",
        "password": "secret123",
        "business_name": "Acme4",
        "ein": "77-9999999",
        "contact_email": "biz4@test.com",
    })
    assert resp.status_code == 409
