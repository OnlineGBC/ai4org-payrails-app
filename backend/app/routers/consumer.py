from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import Optional

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.ledger import WalletBalanceResponse
from app.services.consumer_payment_service import consumer_pay
from app.services.wallet_service import get_wallet_balance, wallet_credit

router = APIRouter(tags=["consumer"])


class ConsumerPayRequest(BaseModel):
    merchant_id: str
    amount: Decimal
    description: Optional[str] = None
    idempotency_key: str
    preferred_rail: Optional[str] = None


@router.post("/consumer/pay")
def consumer_pay_endpoint(
    payload: ConsumerPayRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only consumers can make wallet payments",
        )
    try:
        return consumer_pay(
            db,
            current_user.id,
            merchant_id=payload.merchant_id,
            amount=payload.amount,
            idempotency_key=payload.idempotency_key,
            description=payload.description,
            preferred_rail=payload.preferred_rail,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/consumer/wallet/balance", response_model=WalletBalanceResponse)
def get_consumer_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    balance = get_wallet_balance(db, current_user.id)
    return WalletBalanceResponse(user_id=current_user.id, balance=balance)


@router.post("/consumer/wallet/topup", response_model=WalletBalanceResponse)
def topup_wallet(
    amount: Decimal,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be positive",
        )
    wallet_credit(db, current_user.id, amount, description="Wallet top-up")
    balance = get_wallet_balance(db, current_user.id)
    return WalletBalanceResponse(user_id=current_user.id, balance=balance)
