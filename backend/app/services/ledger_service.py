from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.models.ledger import Ledger
from app.services.units import to_base_units, from_base_units


def get_balance(db: Session, merchant_id: str, asset_code: str = "USD") -> Decimal:
    """Balance for a merchant in a given asset.

    USD sums the legacy Decimal `amount` column (exact at 2 decimals); other
    assets sum integer `amount_base_units` and convert back. Always filtered by
    asset so USD and stablecoin balances never mix.
    """
    col = Ledger.amount if asset_code == "USD" else Ledger.amount_base_units
    result = db.query(
        func.sum(case((Ledger.entry_type == "credit", col), else_=-col))
    ).filter(
        Ledger.merchant_id == merchant_id,
        Ledger.asset_code == asset_code,
    ).scalar()
    if result is None:
        return Decimal("0")
    if asset_code == "USD":
        return Decimal(str(result))
    return from_base_units(int(result), asset_code)


def _new_entry(
    *, merchant_id: Optional[str], user_id: Optional[str], entry_type: str,
    amount: Decimal, new_balance: Decimal, asset_code: str,
    transaction_id: Optional[str], description: Optional[str],
) -> Ledger:
    is_usd = asset_code == "USD"
    return Ledger(
        merchant_id=merchant_id,
        user_id=user_id,
        transaction_id=transaction_id,
        entry_type=entry_type,
        # Legacy Decimal columns are USD-only; stablecoins use base units.
        amount=(amount if is_usd else None),
        balance_after=(new_balance if is_usd else None),
        asset_code=asset_code,
        amount_base_units=to_base_units(amount, asset_code),
        balance_after_base_units=to_base_units(new_balance, asset_code),
        description=description,
    )


def record_debit(
    db: Session,
    merchant_id: str,
    amount: Decimal,
    transaction_id: Optional[str] = None,
    description: Optional[str] = None,
    asset_code: str = "USD",
) -> Ledger:
    current_balance = get_balance(db, merchant_id, asset_code)
    entry = _new_entry(
        merchant_id=merchant_id, user_id=None, entry_type="debit",
        amount=amount, new_balance=current_balance - amount, asset_code=asset_code,
        transaction_id=transaction_id, description=description,
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
    asset_code: str = "USD",
) -> Ledger:
    current_balance = get_balance(db, merchant_id, asset_code)
    entry = _new_entry(
        merchant_id=merchant_id, user_id=None, entry_type="credit",
        amount=amount, new_balance=current_balance + amount, asset_code=asset_code,
        transaction_id=transaction_id, description=description,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def _entry_amount(entry: Ledger) -> Decimal:
    if entry.amount is not None:
        return Decimal(str(entry.amount))
    return from_base_units(int(entry.amount_base_units or 0), entry.asset_code or "USD")


def reverse_entry(db: Session, ledger_id: str, description: Optional[str] = None) -> Ledger:
    original = db.query(Ledger).filter(Ledger.id == ledger_id).first()
    if not original:
        raise ValueError("Ledger entry not found")

    amount = _entry_amount(original)
    asset_code = original.asset_code or "USD"
    desc = description or f"Reversal of {ledger_id}"
    if original.entry_type == "debit":
        return record_credit(db, original.merchant_id, amount, original.transaction_id, desc, asset_code)
    return record_debit(db, original.merchant_id, amount, original.transaction_id, desc, asset_code)
