from decimal import Decimal
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.merchant import Merchant
from app.models.bank_config import BankConfig
from app.schemas.transaction import PaymentCreate, PaymentResponse, PaymentListResponse
from app.services.rail_selector import select_rail
from app.services.bank.mock_bank import mock_bank_service
from app.services.bank.schemas import TransferRequest
from app.services.ledger_service import record_debit, record_credit
from app.services.event_service import log_event


def create_payment(db: Session, payload: PaymentCreate) -> PaymentResponse:
    # Idempotency check
    existing = (
        db.query(Transaction)
        .filter(Transaction.idempotency_key == payload.idempotency_key)
        .first()
    )
    if existing:
        return PaymentResponse.model_validate(existing)

    # Validate merchants
    sender = db.query(Merchant).filter(Merchant.id == payload.sender_merchant_id).first()
    if not sender or sender.onboarding_status != "active":
        raise ValueError("Sender merchant not found or not active")

    receiver = db.query(Merchant).filter(Merchant.id == payload.receiver_merchant_id).first()
    if not receiver or receiver.onboarding_status != "active":
        raise ValueError("Receiver merchant not found or not active")

    # Get bank config for rail selection
    bank_config = db.query(BankConfig).filter(BankConfig.is_active == True).first()
    if not bank_config:
        raise ValueError("No active bank configuration found")

    # Select rail
    rail = select_rail(
        amount=payload.amount,
        supported_rails=bank_config.supported_rails,
        preferred_rail=payload.preferred_rail,
    )
    if not rail:
        raise ValueError("No suitable payment rail available for this amount")

    # Create transaction record
    txn = Transaction(
        sender_merchant_id=payload.sender_merchant_id,
        receiver_merchant_id=payload.receiver_merchant_id,
        sender_bank_account_id=payload.sender_bank_account_id,
        receiver_bank_account_id=payload.receiver_bank_account_id,
        amount=payload.amount,
        currency=payload.currency,
        rail=rail,
        status="processing",
        idempotency_key=payload.idempotency_key,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)

    log_event(db, "payment.initiated", "payment_service", txn.id, {
        "rail": rail, "amount": str(payload.amount),
    })

    # Call mock bank
    transfer_request = TransferRequest(
        sender_account_id=payload.sender_bank_account_id or sender.id,
        receiver_account_id=payload.receiver_bank_account_id or receiver.id,
        amount=payload.amount,
        rail=rail,
        idempotency_key=payload.idempotency_key,
    )

    result = mock_bank_service.initiate_transfer(transfer_request)

    # Update transaction with result
    txn.reference_id = result.reference_id
    txn.status = result.status
    txn.failure_reason = result.failure_reason
    db.commit()

    # If completed, create ledger entries
    if result.status == "completed":
        record_debit(db, payload.sender_merchant_id, payload.amount, txn.id, "Payment sent")
        record_credit(db, payload.receiver_merchant_id, payload.amount, txn.id, "Payment received")
        log_event(db, "payment.completed", "payment_service", txn.id)
    elif result.status == "failed":
        log_event(db, "payment.failed", "payment_service", txn.id, {
            "reason": result.failure_reason,
        })

    db.refresh(txn)
    return PaymentResponse.model_validate(txn)


def get_payment(db: Session, payment_id: str) -> Optional[PaymentResponse]:
    txn = db.query(Transaction).filter(Transaction.id == payment_id).first()
    if not txn:
        return None
    return PaymentResponse.model_validate(txn)


def list_payments(
    db: Session,
    merchant_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    rail_filter: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> PaymentListResponse:
    query = db.query(Transaction)

    if merchant_id:
        query = query.filter(
            (Transaction.sender_merchant_id == merchant_id)
            | (Transaction.receiver_merchant_id == merchant_id)
        )
    if status_filter:
        query = query.filter(Transaction.status == status_filter)
    if rail_filter:
        query = query.filter(Transaction.rail == rail_filter)

    total = query.count()
    items = (
        query.order_by(Transaction.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaymentListResponse(
        items=[PaymentResponse.model_validate(t) for t in items],
        total=total,
        page=page,
        page_size=page_size,
    )


def cancel_payment(db: Session, payment_id: str) -> PaymentResponse:
    txn = db.query(Transaction).filter(Transaction.id == payment_id).first()
    if not txn:
        raise ValueError("Transaction not found")
    if txn.status not in ("pending", "processing"):
        raise ValueError(f"Cannot cancel transaction in status: {txn.status}")

    txn.status = "cancelled"
    db.commit()
    db.refresh(txn)

    log_event(db, "payment.cancelled", "payment_service", txn.id)
    return PaymentResponse.model_validate(txn)
