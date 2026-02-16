from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.payment_request import (
    PaymentRequestCreate,
    PaymentRequestResponse,
    ConsumerPayRequest,
)
from app.schemas.ledger import BalanceResponse, WalletBalanceResponse
from app.services.consumer_payment_service import (
    create_payment_request,
    get_payment_request,
    consumer_pay,
)
from app.services.wallet_service import get_wallet_balance, wallet_credit

router = APIRouter(tags=["consumer"])


@router.post(
    "/merchants/{merchant_id}/payment-requests",
    response_model=PaymentRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_payment_request_endpoint(
    merchant_id: str,
    payload: PaymentRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "merchant_admin" or current_user.merchant_id != merchant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the merchant admin can create payment requests",
        )
    try:
        return create_payment_request(db, merchant_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/payment-requests/{request_id}",
    response_model=PaymentRequestResponse,
)
def get_payment_request_endpoint(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = get_payment_request(db, request_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment request not found",
        )
    return result


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
        return consumer_pay(db, current_user.id, payload)
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
