from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.models.ledger import Ledger


def get_wallet_balance(db: Session, user_id: str) -> Decimal:
    result = db.query(
        func.sum(
            case(
                (Ledger.entry_type == "credit", Ledger.amount),
                else_=-Ledger.amount,
            )
        )
    ).filter(Ledger.user_id == user_id).scalar()
    return Decimal(str(result)) if result is not None else Decimal("0")


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
