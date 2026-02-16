"""
Seed script — run from backend/ with: python -m app.seed
Creates: 1 BankConfig, 2 Merchants, 2 Merchant Users, 2 Consumer Users,
2 BankAccounts, initial $100K merchant balances, $500 consumer wallets.
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


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # BankConfig
        if not db.query(BankConfig).first():
            bc = BankConfig(
                id="bank-config-001",
                bank_name="MockBank",
                supported_rails="fednow,rtp,ach,card",
                fednow_limit=Decimal("500000"),
                rtp_limit=Decimal("1000000"),
                ach_limit=Decimal("10000000"),
                is_active=True,
            )
            db.add(bc)
            db.commit()
            print("Created BankConfig: MockBank")

        # Merchants
        m1 = db.query(Merchant).filter(Merchant.id == "merchant-001").first()
        if not m1:
            m1 = Merchant(
                id="merchant-001",
                name="Acme Corp",
                ein="12-3456789",
                contact_email="admin@acme.com",
                onboarding_status="active",
                kyb_status="approved",
            )
            db.add(m1)
            db.commit()
            print("Created Merchant: Acme Corp")

        m2 = db.query(Merchant).filter(Merchant.id == "merchant-002").first()
        if not m2:
            m2 = Merchant(
                id="merchant-002",
                name="Globex Inc",
                ein="98-7654321",
                contact_email="admin@globex.com",
                onboarding_status="active",
                kyb_status="approved",
            )
            db.add(m2)
            db.commit()
            print("Created Merchant: Globex Inc")

        # Users
        u1 = db.query(User).filter(User.email == "admin@acme.com").first()
        if not u1:
            u1 = User(
                id="user-001",
                email="admin@acme.com",
                hashed_password=hash_password("password123"),
                role="merchant_admin",
                merchant_id="merchant-001",
            )
            db.add(u1)
            db.commit()
            print("Created User: admin@acme.com / password123")

        u2 = db.query(User).filter(User.email == "admin@globex.com").first()
        if not u2:
            u2 = User(
                id="user-002",
                email="admin@globex.com",
                hashed_password=hash_password("password123"),
                role="merchant_admin",
                merchant_id="merchant-002",
            )
            db.add(u2)
            db.commit()
            print("Created User: admin@globex.com / password123")

        # Bank Accounts
        ba1 = db.query(BankAccount).filter(BankAccount.id == "bank-acct-001").first()
        if not ba1:
            ba1 = BankAccount(
                id="bank-acct-001",
                merchant_id="merchant-001",
                bank_name="MockBank",
                routing_number="021000021",
                encrypted_account_number=encrypt_value("1234567890"),
                account_type="checking",
                verification_status="verified",
            )
            db.add(ba1)
            db.commit()
            print("Created BankAccount for Acme Corp")

        ba2 = db.query(BankAccount).filter(BankAccount.id == "bank-acct-002").first()
        if not ba2:
            ba2 = BankAccount(
                id="bank-acct-002",
                merchant_id="merchant-002",
                bank_name="MockBank",
                routing_number="021000021",
                encrypted_account_number=encrypt_value("0987654321"),
                account_type="checking",
                verification_status="verified",
            )
            db.add(ba2)
            db.commit()
            print("Created BankAccount for Globex Inc")

        # Consumer Users
        c1 = db.query(User).filter(User.email == "consumer1@test.com").first()
        if not c1:
            c1 = User(
                id="user-consumer-001",
                email="consumer1@test.com",
                hashed_password=hash_password("password123"),
                role="user",
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
            )
            db.add(c2)
            db.commit()
            print("Created Consumer: consumer2@test.com / password123")

        # Initial balances — $100K each for merchants
        from app.models.ledger import Ledger
        if not db.query(Ledger).filter(Ledger.merchant_id == "merchant-001").first():
            record_credit(db, "merchant-001", Decimal("100000.00"), description="Initial seed balance")
            print("Credited $100,000 to Acme Corp")

        if not db.query(Ledger).filter(Ledger.merchant_id == "merchant-002").first():
            record_credit(db, "merchant-002", Decimal("100000.00"), description="Initial seed balance")
            print("Credited $100,000 to Globex Inc")

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
