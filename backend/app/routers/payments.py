from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.transaction import PaymentCreate, PaymentResponse, PaymentListResponse
from app.schemas.ledger import BalanceResponse
from app.services.payment_service import create_payment, get_payment, list_payments, cancel_payment
from app.services.ledger_service import get_balance

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def send_payment(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return create_payment(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/balance", response_model=BalanceResponse)
def check_balance(
    merchant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    balance = get_balance(db, merchant_id)
    return BalanceResponse(merchant_id=merchant_id, balance=balance)


@router.get("", response_model=PaymentListResponse)
def get_payments(
    merchant_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    rail: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_payments(db, merchant_id, status_filter, rail, page, page_size)


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment_by_id(
    payment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = get_payment(db, payment_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return result


@router.post("/{payment_id}/cancel", response_model=PaymentResponse)
def cancel_payment_endpoint(
    payment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return cancel_payment(db, payment_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/payouts", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payout(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return create_payment(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
