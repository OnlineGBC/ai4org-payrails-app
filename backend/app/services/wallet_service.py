from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.models.ledger import Ledger
from app.services.units import to_base_units, from_base_units


def get_wallet_balance(db: Session, user_id: str, asset_code: str = "USD") -> Decimal:
    """Consumer wallet balance for a user in a given asset (asset-filtered)."""
    col = Ledger.amount if asset_code == "USD" else Ledger.amount_base_units
    result = db.query(
        func.sum(case((Ledger.entry_type == "credit", col), else_=-col))
    ).filter(
        Ledger.user_id == user_id,
        Ledger.asset_code == asset_code,
    ).scalar()
    if result is None:
        return Decimal("0")
    if asset_code == "USD":
        return Decimal(str(result))
    return from_base_units(int(result), asset_code)


def _new_entry(
    *, user_id: str, entry_type: str, amount: Decimal, new_balance: Decimal,
    asset_code: str, transaction_id: Optional[str], description: Optional[str],
) -> Ledger:
    is_usd = asset_code == "USD"
    return Ledger(
        user_id=user_id,
        transaction_id=transaction_id,
        entry_type=entry_type,
        amount=(amount if is_usd else None),
        balance_after=(new_balance if is_usd else None),
        asset_code=asset_code,
        amount_base_units=to_base_units(amount, asset_code),
        balance_after_base_units=to_base_units(new_balance, asset_code),
        description=description,
    )


def wallet_debit(
    db: Session,
    user_id: str,
    amount: Decimal,
    transaction_id: Optional[str] = None,
    description: Optional[str] = None,
    asset_code: str = "USD",
) -> Ledger:
    current_balance = get_wallet_balance(db, user_id, asset_code)
    if amount > current_balance:
        raise ValueError("Insufficient wallet balance")
    entry = _new_entry(
        user_id=user_id, entry_type="debit", amount=amount,
        new_balance=current_balance - amount, asset_code=asset_code,
        transaction_id=transaction_id, description=description,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def wallet_credit(
    db: Session,
    user_id: str,
    amount: Decimal,
    transaction_id: Optional[str] = None,
    description: Optional[str] = None,
    asset_code: str = "USD",
) -> Ledger:
    current_balance = get_wallet_balance(db, user_id, asset_code)
    entry = _new_entry(
        user_id=user_id, entry_type="credit", amount=amount,
        new_balance=current_balance + amount, asset_code=asset_code,
        transaction_id=transaction_id, description=description,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
