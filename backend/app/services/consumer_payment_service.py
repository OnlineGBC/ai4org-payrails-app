from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session

from app.models.payment_request import PaymentRequest
from app.models.merchant import Merchant
from app.models.transaction import Transaction
from app.models.bank_config import BankConfig
from app.schemas.payment_request import PaymentRequestCreate, PaymentRequestResponse, ConsumerPayRequest
from app.services.rail_selector import select_rail
from app.services.bank.mock_bank import mock_bank_service
from app.services.bank.schemas import TransferRequest
from app.services.wallet_service import wallet_debit, get_wallet_balance
from app.services.ledger_service import record_credit
from app.services.event_service import log_event


def create_payment_request(
    db: Session, merchant_id: str, payload: PaymentRequestCreate
) -> PaymentRequestResponse:
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant or merchant.onboarding_status != "active":
        raise ValueError("Merchant not found or not active")

    expires_at = datetime.utcnow() + timedelta(minutes=payload.expires_in_minutes)

    pr = PaymentRequest(
        merchant_id=merchant_id,
        amount=payload.amount,
        currency=payload.currency,
        description=payload.description,
        status="pending",
        expires_at=expires_at,
    )
    db.add(pr)
    db.commit()
    db.refresh(pr)

    return PaymentRequestResponse(
        id=pr.id,
        merchant_id=pr.merchant_id,
        merchant_name=merchant.name,
        amount=pr.amount,
        currency=pr.currency,
        description=pr.description,
        status=pr.status,
        expires_at=pr.expires_at,
        created_at=pr.created_at,
        updated_at=pr.updated_at,
    )


def get_payment_request(
    db: Session, request_id: str
) -> Optional[PaymentRequestResponse]:
    pr = db.query(PaymentRequest).filter(PaymentRequest.id == request_id).first()
    if not pr:
        return None

    merchant = db.query(Merchant).filter(Merchant.id == pr.merchant_id).first()
    merchant_name = merchant.name if merchant else None

    return PaymentRequestResponse(
        id=pr.id,
        merchant_id=pr.merchant_id,
        merchant_name=merchant_name,
        amount=pr.amount,
        currency=pr.currency,
        description=pr.description,
        status=pr.status,
        expires_at=pr.expires_at,
        created_at=pr.created_at,
        updated_at=pr.updated_at,
    )


def consumer_pay(
    db: Session, user_id: str, payload: ConsumerPayRequest
) -> dict:
    # Idempotency check
    existing = (
        db.query(Transaction)
        .filter(Transaction.idempotency_key == payload.idempotency_key)
        .first()
    )
    if existing:
        return {"transaction_id": existing.id, "status": existing.status}

    # Load and validate payment request
    pr = db.query(PaymentRequest).filter(PaymentRequest.id == payload.payment_request_id).first()
    if not pr:
        raise ValueError("Payment request not found")
    if pr.status != "pending":
        raise ValueError(f"Payment request is {pr.status}, not pending")
    if pr.expires_at and pr.expires_at < datetime.utcnow():
        pr.status = "expired"
        db.commit()
        raise ValueError("Payment request has expired")

    # Check consumer wallet balance
    balance = get_wallet_balance(db, user_id)
    if balance < pr.amount:
        raise ValueError("Insufficient wallet balance")

    # Get bank config for rail selection
    bank_config = db.query(BankConfig).filter(BankConfig.is_active == True).first()
    if not bank_config:
        raise ValueError("No active bank configuration found")

    # Select rail
    rail = select_rail(
        amount=pr.amount,
        supported_rails=bank_config.supported_rails,
        preferred_rail=payload.preferred_rail,
    )
    if not rail:
        raise ValueError("No suitable payment rail available for this amount")

    # Create transaction
    txn = Transaction(
        sender_user_id=user_id,
        receiver_merchant_id=pr.merchant_id,
        amount=pr.amount,
        currency=pr.currency,
        rail=rail,
        status="processing",
        idempotency_key=payload.idempotency_key,
        payment_request_id=pr.id,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)

    log_event(db, "consumer_payment.initiated", "consumer_payment_service", txn.id, {
        "rail": rail, "amount": str(pr.amount), "user_id": user_id,
    })

    # Call mock bank
    merchant = db.query(Merchant).filter(Merchant.id == pr.merchant_id).first()
    transfer_request = TransferRequest(
        sender_account_id=user_id,
        receiver_account_id=merchant.id if merchant else pr.merchant_id,
        amount=pr.amount,
        rail=rail,
        idempotency_key=payload.idempotency_key,
    )

    result = mock_bank_service.initiate_transfer(transfer_request)

    # Update transaction with result
    txn.reference_id = result.reference_id
    txn.status = result.status
    txn.failure_reason = result.failure_reason
    db.commit()

    # If completed, update ledger entries and payment request
    if result.status == "completed":
        wallet_debit(db, user_id, pr.amount, txn.id, f"Payment to {merchant.name if merchant else pr.merchant_id}")
        record_credit(db, pr.merchant_id, pr.amount, txn.id, f"Payment from consumer {user_id}")
        pr.status = "completed"
        db.commit()
        log_event(db, "consumer_payment.completed", "consumer_payment_service", txn.id)
    elif result.status == "failed":
        log_event(db, "consumer_payment.failed", "consumer_payment_service", txn.id, {
            "reason": result.failure_reason,
        })

    return {
        "transaction_id": txn.id,
        "status": txn.status,
        "reference_id": txn.reference_id,
        "failure_reason": txn.failure_reason,
    }
