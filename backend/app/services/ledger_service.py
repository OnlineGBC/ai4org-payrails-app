from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.ledger import Ledger


def get_balance(db: Session, merchant_id: str) -> Decimal:
    last_entry = (
        db.query(Ledger)
        .filter(Ledger.merchant_id == merchant_id)
        .order_by(Ledger.created_at.desc())
        .first()
    )
    if last_entry:
        return Decimal(str(last_entry.balance_after))
    return Decimal("0")


def record_debit(
    db: Session,
    merchant_id: str,
    amount: Decimal,
    transaction_id: Optional[str] = None,
    description: Optional[str] = None,
) -> Ledger:
    current_balance = get_balance(db, merchant_id)
    new_balance = current_balance - amount

    entry = Ledger(
        merchant_id=merchant_id,
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


def record_credit(
    db: Session,
    merchant_id: str,
    amount: Decimal,
    transaction_id: Optional[str] = None,
    description: Optional[str] = None,
) -> Ledger:
    current_balance = get_balance(db, merchant_id)
    new_balance = current_balance + amount

    entry = Ledger(
        merchant_id=merchant_id,
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


def reverse_entry(db: Session, ledger_id: str, description: Optional[str] = None) -> Ledger:
    original = db.query(Ledger).filter(Ledger.id == ledger_id).first()
    if not original:
        raise ValueError("Ledger entry not found")

    reverse_type = "credit" if original.entry_type == "debit" else "debit"
    if reverse_type == "credit":
        return record_credit(
            db, original.merchant_id, Decimal(str(original.amount)),
            original.transaction_id, description or f"Reversal of {ledger_id}",
        )
    else:
        return record_debit(
            db, original.merchant_id, Decimal(str(original.amount)),
            original.transaction_id, description or f"Reversal of {ledger_id}",
        )
