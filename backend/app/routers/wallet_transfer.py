from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import Optional

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.transaction import Transaction
from app.services.wallet_service import get_wallet_balance, wallet_debit, wallet_credit
from app.services.ledger_service import get_balance, record_debit
from app.services import description_service, notification_service

router = APIRouter(tags=["wallet"])


class WalletSendRequest(BaseModel):
    receiver_user_id: str
    amount: Decimal
    idempotency_key: str
    description: Optional[str] = None


@router.post("/wallet/send")
def wallet_send(
    payload: WalletSendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("user", "merchant_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to send wallet payments",
        )

    # Idempotency check
    existing = (
        db.query(Transaction)
        .filter(Transaction.idempotency_key == payload.idempotency_key)
        .first()
    )
    if existing:
        return {
            "transaction_id": existing.id,
            "status": existing.status,
            "amount": str(existing.amount),
            "description": existing.description,
        }

    # Validate receiver
    receiver = db.query(User).filter(User.id == payload.receiver_user_id).first()
    if not receiver or receiver.role != "user":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Receiver not found or is not a consumer account",
        )

    amount = payload.amount

    # Check sender balance
    if current_user.role == "user":
        balance = get_wallet_balance(db, current_user.id)
        if balance < amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient wallet balance",
            )
    else:  # merchant_admin
        if not current_user.merchant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No merchant associated with your account",
            )
        balance = get_balance(db, current_user.merchant_id)
        if balance < amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient merchant balance",
            )

    # Create transaction record
    txn = Transaction(
        sender_user_id=current_user.id if current_user.role == "user" else None,
        sender_merchant_id=current_user.merchant_id if current_user.role == "merchant_admin" else None,
        receiver_user_id=payload.receiver_user_id,
        receiver_merchant_id=None,
        amount=amount,
        currency="USD",
        rail="wallet",
        status="completed",
        idempotency_key=payload.idempotency_key,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)

    # Debit sender
    if current_user.role == "user":
        wallet_debit(db, current_user.id, amount, txn.id, f"Sent to {receiver.email}")
    else:
        record_debit(
            db, current_user.merchant_id, amount, txn.id,
            f"Sent to consumer {receiver.email}",
        )

    # Credit receiver
    sender_label = current_user.email or current_user.merchant_id or "unknown"
    wallet_credit(
        db, payload.receiver_user_id, amount, txn.id,
        f"Received from {sender_label}",
    )

    # AI-generated description
    generated_desc = description_service.generate_description(
        receiver.email, float(amount), "wallet", payload.description
    )
    txn.description = generated_desc
    db.commit()

    # Notify receiver
    notification_service.notify_transaction(
        db, payload.receiver_user_id, txn.id, "completed",
        float(amount), receiver.email, "wallet", generated_desc,
    )

    return {
        "transaction_id": txn.id,
        "status": txn.status,
        "amount": str(txn.amount),
        "description": txn.description,
    }
