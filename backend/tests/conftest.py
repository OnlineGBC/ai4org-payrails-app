import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from decimal import Decimal

from app.database import Base, get_db
from app.main import app
from app.models.merchant import Merchant
from app.models.user import User
from app.models.bank_config import BankConfig
from app.models.bank_account import BankAccount
from app.services.auth_service import hash_password, create_access_token
from app.services.ledger_service import record_credit
from app.utils.encryption import encrypt_value

TEST_DB_URL = "sqlite:///./test.db"


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def seed_data(db_session):
    """Create merchants, users, bank config, bank accounts, and initial balances."""
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

    m1 = Merchant(
        id="merchant-001",
        name="Acme Corp",
        ein="12-3456789",
        contact_email="admin@acme.com",
        onboarding_status="active",
        kyb_status="approved",
    )
    m2 = Merchant(
        id="merchant-002",
        name="Globex Inc",
        ein="98-7654321",
        contact_email="admin@globex.com",
        onboarding_status="active",
        kyb_status="approved",
    )
    db_session.add_all([m1, m2])

    u1 = User(
        id="user-001",
        email="admin@acme.com",
        hashed_password=hash_password("password123"),
        role="merchant_admin",
        merchant_id="merchant-001",
    )
    db_session.add(u1)

    ba1 = BankAccount(
        id="bank-acct-001",
        merchant_id="merchant-001",
        bank_name="MockBank",
        routing_number="021000021",
        encrypted_account_number=encrypt_value("1234567890"),
        account_type="checking",
        verification_status="verified",
    )
    ba2 = BankAccount(
        id="bank-acct-002",
        merchant_id="merchant-002",
        bank_name="MockBank",
        routing_number="021000021",
        encrypted_account_number=encrypt_value("0987654321"),
        account_type="checking",
        verification_status="verified",
    )
    db_session.add_all([ba1, ba2])
    db_session.commit()

    record_credit(db_session, "merchant-001", Decimal("100000.00"), description="Seed")
    record_credit(db_session, "merchant-002", Decimal("100000.00"), description="Seed")

    return {"merchants": [m1, m2], "users": [u1], "bank_accounts": [ba1, ba2]}


def get_auth_header(user_id="user-001", email="admin@acme.com", role="merchant_admin"):
    token = create_access_token({"sub": user_id, "email": email, "role": role})
    return {"Authorization": f"Bearer {token}"}
