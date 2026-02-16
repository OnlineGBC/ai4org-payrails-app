from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session

from app.models.ledger import Ledger


def get_wallet_balance(db: Session, user_id: str) -> Decimal:
    last_entry = (
        db.query(Ledger)
        .filter(Ledger.user_id == user_id)
        .order_by(Ledger.created_at.desc())
        .first()
    )
    if last_entry:
        return Decimal(str(last_entry.balance_after))
    return Decimal("0")


def wallet_debit(
    db: Session,
    user_id: str,
    amount: Decimal,
    transaction_id: Optional[str] = None,
    description: Optional[str] = None,
) -> Ledger:
    current_balance = get_wallet_balance(db, user_id)
    if amount > current_balance:
        raise ValueError("Insufficient wallet balance")
    new_balance = current_balance - amount

    entry = Ledger(
        user_id=user_id,
        transaction_id=transaction_id,
        entry_type="debit",
        amount=amount,
        balance_after=new_balance,
        description=description,
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
) -> Ledger:
    current_balance = get_wallet_balance(db, user_id)
    new_balance = current_balance + amount

    entry = Ledger(
        user_id=user_id,
        transaction_id=transaction_id,
        entry_type="credit",
        amount=amount,
        balance_after=new_balance,
        description=description,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
