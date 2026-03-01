"""
Seed script — run from backend/ with: python -m app.seed
Creates: 15 BankConfigs, 15 Merchants, 15 Merchant Users, 2 Consumer Users,
15 BankAccounts, initial $100K merchant balances, $500 consumer wallets.
"""
from decimal import Decimal
from app.database import engine, SessionLocal, Base
from app.models.bank_config import BankConfig
from app.models.merchant import Merchant
from app.models.user import User
from app.models.bank_account import BankAccount
from app.services.auth_service import hash_password
from app.services.ledger_service import record_credit
from app.services.wallet_service import wallet_credit
from app.utils.encryption import encrypt_value


# ---------------------------------------------------------------------------
# Helper data
# ---------------------------------------------------------------------------

BANK_CONFIGS = [
    ("bank-config-001", "Pinnacle BankTest"),
    ("bank-config-002", "American BankTest"),
    ("bank-config-003", "USBankTest"),
    ("bank-config-004", "BNYMellonTest"),
    ("bank-config-005", "BancorpTest"),
    ("bank-config-006", "SouthStateTest"),
    ("bank-config-007", "SimmonsTest"),
    ("bank-config-008", "FirstSourceTest"),
    ("bank-config-009", "Y12FedCredTest"),
    ("bank-config-010", "YakimaTest"),
    ("bank-config-011", "YumaTest"),
    ("bank-config-012", "JPMorganTest"),
    ("bank-config-013", "WellsFargoTest"),
    ("bank-config-014", "PNCTest"),
    ("bank-config-015", "TruistTest"),
]

MERCHANTS = [
    # (id, name, ein, bank_name)
    ("merchant-001", "Acme Corp",               "12-3456789", "Pinnacle BankTest"),
    ("merchant-002", "Globex Inc",              "98-7654321", "American BankTest"),
    ("merchant-003", "WalmartTestCorp",         "20-1234567", "USBankTest"),
    ("merchant-004", "FoodLionTestCorp",        "21-2345678", "BNYMellonTest"),
    ("merchant-005", "TargetTestCorp",          "22-3456789", "BancorpTest"),
    ("merchant-006", "McDonaldsTestCorp",       "23-4567890", "SouthStateTest"),
    ("merchant-007", "CostcoTestCorp",          "24-5678901", "SimmonsTest"),
    ("merchant-008", "WesternUnionTestCorp",    "25-6789012", "FirstSourceTest"),
    ("merchant-009", "NetflixTestCorp",         "26-7890123", "Y12FedCredTest"),
    ("merchant-010", "BurgerKingTestCorp",      "27-8901234", "YakimaTest"),
    ("merchant-011", "AldiTestCorp",            "28-9012345", "YumaTest"),
    ("merchant-012", "DollarGeneralTestCorp",   "29-0123456", "JPMorganTest"),
    ("merchant-013", "SubwayTestCorp",          "30-1234567", "WellsFargoTest"),
    ("merchant-014", "NikeTestCorp",            "31-2345678", "PNCTest"),
    ("merchant-015", "BoostMobileTestCorp",     "32-3456789", "TruistTest"),
]

MERCHANT_USERS = [
    # (user_id, email, merchant_id, phone)
    ("user-001", "admin@acme.com",              "merchant-001", "+15550000001"),
    ("user-002", "admin@globex.com",            "merchant-002", "+15550000002"),
    ("user-003", "admin@walmart.testcorp",      "merchant-003", "+15550000003"),
    ("user-004", "admin@foodlion.testcorp",     "merchant-004", "+15550000004"),
    ("user-005", "admin@target.testcorp",       "merchant-005", "+15550000005"),
    ("user-006", "admin@mcdonalds.testcorp",    "merchant-006", "+15550000006"),
    ("user-007", "admin@costco.testcorp",       "merchant-007", "+15550000007"),
    ("user-008", "admin@westernunion.testcorp", "merchant-008", "+15550000008"),
    ("user-009", "admin@netflix.testcorp",      "merchant-009", "+15550000009"),
    ("user-010", "admin@burgerking.testcorp",   "merchant-010", "+15550000010"),
    ("user-011", "admin@aldi.testcorp",         "merchant-011", "+15550000011"),
    ("user-012", "admin@dollargeneral.testcorp","merchant-012", "+15550000012"),
    ("user-013", "admin@subway.testcorp",       "merchant-013", "+15550000013"),
    ("user-014", "admin@nike.testcorp",         "merchant-014", "+15550000014"),
    ("user-015", "admin@boostmobile.testcorp",  "merchant-015", "+15550000015"),
]

BANK_ACCOUNTS = [
    # (acct_id, merchant_id, bank_name, routing, account_number)
    ("bank-acct-001", "merchant-001", "Pinnacle BankTest",  "021000021", "1234567890"),
    ("bank-acct-002", "merchant-002", "American BankTest",  "071000013", "0987654321"),
    ("bank-acct-003", "merchant-003", "USBankTest",         "091000022", "2000000001"),
    ("bank-acct-004", "merchant-004", "BNYMellonTest",      "021000018", "2000000002"),
    ("bank-acct-005", "merchant-005", "BancorpTest",        "031100209", "2000000003"),
    ("bank-acct-006", "merchant-006", "SouthStateTest",     "053200983", "2000000004"),
    ("bank-acct-007", "merchant-007", "SimmonsTest",        "082900872", "2000000005"),
    ("bank-acct-008", "merchant-008", "FirstSourceTest",    "074900356", "2000000006"),
    ("bank-acct-009", "merchant-009", "Y12FedCredTest",     "064000059", "2000000007"),
    ("bank-acct-010", "merchant-010", "YakimaTest",         "125108405", "2000000008"),
    ("bank-acct-011", "merchant-011", "YumaTest",           "122400724", "2000000009"),
    ("bank-acct-012", "merchant-012", "JPMorganTest",       "021000021", "2000000010"),
    ("bank-acct-013", "merchant-013", "WellsFargoTest",     "121042882", "2000000011"),
    ("bank-acct-014", "merchant-014", "PNCTest",            "043000096", "2000000012"),
    ("bank-acct-015", "merchant-015", "TruistTest",         "053101121", "2000000013"),
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # ------------------------------------------------------------------ #
        # BankConfigs
        # ------------------------------------------------------------------ #
        for bc_id, bc_name in BANK_CONFIGS:
            if not db.query(BankConfig).filter(BankConfig.id == bc_id).first():
                bc = BankConfig(
                    id=bc_id,
                    bank_name=bc_name,
                    supported_rails="fednow,rtp,ach,card",
                    fednow_limit=Decimal("500000"),
                    rtp_limit=Decimal("1000000"),
                    ach_limit=Decimal("10000000"),
                    is_active=True,
                )
                db.add(bc)
                db.commit()
                print(f"Created BankConfig: {bc_name}")

        # ------------------------------------------------------------------ #
        # Merchants
        # ------------------------------------------------------------------ #
        for m_id, m_name, m_ein, _ in MERCHANTS:
            if not db.query(Merchant).filter(Merchant.id == m_id).first():
                m = Merchant(
                    id=m_id,
                    name=m_name,
                    ein=m_ein,
                    contact_email=f"admin@{m_name.lower().replace(' ', '')}.com",
                    onboarding_status="active",
                    kyb_status="approved",
                )
                db.add(m)
                db.commit()
                print(f"Created Merchant: {m_name}")

        # ------------------------------------------------------------------ #
        # Merchant Users
        # ------------------------------------------------------------------ #
        for u_id, u_email, m_id, u_phone in MERCHANT_USERS:
            if not db.query(User).filter(User.email == u_email).first():
                u = User(
                    id=u_id,
                    email=u_email,
                    hashed_password=hash_password("password123"),
                    role="merchant_admin",
                    merchant_id=m_id,
                    phone=u_phone,
                )
                db.add(u)
                db.commit()
                print(f"Created User: {u_email} / password123")

        # ------------------------------------------------------------------ #
        # Bank Accounts
        # ------------------------------------------------------------------ #
        for acct_id, m_id, b_name, routing, acct_num in BANK_ACCOUNTS:
            if not db.query(BankAccount).filter(BankAccount.id == acct_id).first():
                ba = BankAccount(
                    id=acct_id,
                    merchant_id=m_id,
                    bank_name=b_name,
                    routing_number=routing,
                    encrypted_account_number=encrypt_value(acct_num),
                    account_type="checking",
                    verification_status="verified",
                )
                db.add(ba)
                db.commit()
                print(f"Created BankAccount {acct_id} for merchant {m_id}")

        # ------------------------------------------------------------------ #
        # Initial merchant balances — $100K each
        # ------------------------------------------------------------------ #
        from app.models.ledger import Ledger
        for m_id, m_name, _, _ in MERCHANTS:
            if not db.query(Ledger).filter(Ledger.merchant_id == m_id).first():
                record_credit(db, m_id, Decimal("100000.00"), description="Initial seed balance")
                print(f"Credited $100,000 to {m_name}")

        # ------------------------------------------------------------------ #
        # Consumer Users
        # ------------------------------------------------------------------ #
        c1 = db.query(User).filter(User.email == "consumer1@test.com").first()
        if not c1:
            c1 = User(
                id="user-consumer-001",
                email="consumer1@test.com",
                hashed_password=hash_password("password123"),
                role="user",
                phone="+15559000001",
            )
            db.add(c1)
            db.commit()
            print("Created Consumer: consumer1@test.com / password123")

        c2 = db.query(User).filter(User.email == "consumer2@test.com").first()
        if not c2:
            c2 = User(
                id="user-consumer-002",
                email="consumer2@test.com",
                hashed_password=hash_password("password123"),
                role="user",
                phone="+15559000002",
            )
            db.add(c2)
            db.commit()
            print("Created Consumer: consumer2@test.com / password123")

        # Consumer wallet balances — $500 each
        if not db.query(Ledger).filter(Ledger.user_id == "user-consumer-001").first():
            wallet_credit(db, "user-consumer-001", Decimal("500.00"), description="Initial wallet balance")
            print("Credited $500 to consumer1@test.com")

        if not db.query(Ledger).filter(Ledger.user_id == "user-consumer-002").first():
            wallet_credit(db, "user-consumer-002", Decimal("500.00"), description="Initial wallet balance")
            print("Credited $500 to consumer2@test.com")

        print("\nSeed complete!")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
