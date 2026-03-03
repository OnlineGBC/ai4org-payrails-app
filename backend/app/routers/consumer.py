import uuid as _uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import Optional

from app.database import get_db
from app.dependencies import get_current_user
from app.models.bank_account import BankAccount
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.ledger import WalletBalanceResponse
from app.services.consumer_payment_service import consumer_pay
from app.services.wallet_service import get_wallet_balance, wallet_credit
from app.services.event_service import log_event
from app.services.bank.mock_bank import mock_bank_service
from app.services.bank.schemas import TransferRequest

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


@router.get("/consumer/users/{user_id}")
def get_consumer_user_info(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Look up a consumer user by ID — used by the pay flow to handle user IDs as payment targets."""
    user = db.query(User).filter(User.id == user_id, User.role == "user").first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"id": user.id, "email": user.email, "merchant_id": user.merchant_id}


@router.post("/consumer/wallet/topup", response_model=WalletBalanceResponse)
def topup_wallet(
    amount: Decimal,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Internal/test endpoint — credits wallet directly with no funding source."""
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be positive",
        )
    wallet_credit(db, current_user.id, amount, description="Wallet top-up")
    balance = get_wallet_balance(db, current_user.id)
    return WalletBalanceResponse(user_id=current_user.id, balance=balance)


class WalletFundRequest(BaseModel):
    bank_account_id: str
    amount: Decimal


class WalletFundResponse(BaseModel):
    user_id: str
    balance: Decimal
    transaction_status: str
    reference_id: str
    failure_reason: Optional[str] = None


@router.post("/consumer/wallet/fund", response_model=WalletFundResponse, status_code=status.HTTP_200_OK)
def fund_wallet(
    payload: WalletFundRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fund wallet by initiating a mock ACH pull from a verified bank account."""
    if current_user.role != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only consumers can fund wallets",
        )
    if payload.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be positive",
        )

    # Validate account belongs to this consumer's merchant and is verified
    account = db.query(BankAccount).filter(
        BankAccount.id == payload.bank_account_id,
        BankAccount.merchant_id == current_user.merchant_id,
    ).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found",
        )
    if account.verification_status != "verified":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bank account is not verified",
        )

    idempotency_key = str(_uuid.uuid4())

    # Initiate ACH pull via mock bank
    transfer_request = TransferRequest(
        sender_account_id=account.id,
        receiver_account_id="payrails-platform",
        amount=payload.amount,
        rail="ach",
        idempotency_key=idempotency_key,
        memo="Wallet funding",
    )
    result = mock_bank_service.initiate_ach(transfer_request)

    # Record transaction for audit trail
    txn = Transaction(
        sender_user_id=current_user.id,
        sender_bank_account_id=account.id,
        amount=payload.amount,
        currency="USD",
        rail="ach",
        status=result.status,
        idempotency_key=idempotency_key,
        reference_id=result.reference_id,
        failure_reason=result.failure_reason,
        description="Wallet funded via ACH",
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)

    if result.status == "completed":
        wallet_credit(
            db, current_user.id, payload.amount, txn.id,
            description=f"Wallet funded via ACH from {account.bank_name or account.routing_number}",
        )
        log_event(db, "wallet.funded", "consumer_router", txn.id, {
            "amount": str(payload.amount),
            "bank_account_id": account.id,
        })
    else:
        log_event(db, "wallet.fund_failed", "consumer_router", txn.id, {
            "reason": result.failure_reason,
        })

    balance = get_wallet_balance(db, current_user.id)
    return WalletFundResponse(
        user_id=current_user.id,
        balance=balance,
        transaction_status=result.status,
        reference_id=result.reference_id,
        failure_reason=result.failure_reason,
    )
