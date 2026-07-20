"""Idempotent demo seeding of stablecoin balances.

Gives every business merchant MERCHANT_AMOUNT and every consumer CONSUMER_AMOUNT
of each in-scope stablecoin (on the merchant entity / consumer wallet
respectively). Idempotent: an owner that already holds a positive balance in an
asset is skipped, so it is safe to run repeatedly (e.g. on startup).
"""
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.user import User
from app.services.ledger_service import record_credit, get_balance
from app.services.wallet_service import wallet_credit, get_wallet_balance

STABLECOIN_ASSETS = ("USDC", "USD1")
MERCHANT_AMOUNT = Decimal("100000")   # per asset, per merchant
CONSUMER_AMOUNT = Decimal("1000")     # per asset, per consumer


def seed_stablecoin_balances(db: Session) -> dict:
    credited = {"merchants": 0, "consumers": 0}

    # Business merchants = merchants that a merchant_admin user is linked to.
    business_merchant_ids = {
        u.merchant_id for u in db.query(User).filter(
            User.role == "merchant_admin", User.merchant_id.isnot(None)
        ).all()
    }
    for mid in business_merchant_ids:
        for asset in STABLECOIN_ASSETS:
            if get_balance(db, mid, asset) <= 0:
                record_credit(db, mid, MERCHANT_AMOUNT, description="Seed stablecoin balance", asset_code=asset)
                credited["merchants"] += 1

    # Consumers.
    for u in db.query(User).filter(User.role == "user").all():
        for asset in STABLECOIN_ASSETS:
            if get_wallet_balance(db, u.id, asset) <= 0:
                wallet_credit(db, u.id, CONSUMER_AMOUNT, description="Seed stablecoin balance", asset_code=asset)
                credited["consumers"] += 1

    return credited
