from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.merchant import Merchant
from app.models.transaction import Transaction
from app.models.bank_config import BankConfig
from app.services.rail_selector import select_rail
from app.services.bank.mock_bank import mock_bank_service
from app.services.bank.schemas import TransferRequest
from app.services.wallet_service import wallet_debit, get_wallet_balance
from app.services.ledger_service import record_credit
from app.services.event_service import log_event
from app.services import description_service, notification_service


def consumer_pay(
    db: Session,
    user_id: str,
    merchant_id: str,
    amount: Decimal,
    idempotency_key: str,
    description: str | None = None,
    preferred_rail: str | None = None,
) -> dict:
    # Idempotency check
    existing = (
        db.query(Transaction)
        .filter(Transaction.idempotency_key == idempotency_key)
        .first()
    )
    if existing:
        return {"transaction_id": existing.id, "status": existing.status}

    # Validate merchant
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant or merchant.onboarding_status != "active":
        raise ValueError("Merchant not found or not active")

    # Check consumer wallet balance
    balance = get_wallet_balance(db, user_id)
    if balance < amount:
        raise ValueError("Insufficient wallet balance")

    # Get bank config for rail selection
    bank_config = db.query(BankConfig).filter(BankConfig.is_active == True).first()
    if not bank_config:
        raise ValueError("No active bank configuration found")

    # Select rail
    rail = select_rail(
        amount=amount,
        supported_rails=bank_config.supported_rails,
        preferred_rail=preferred_rail,
    )
    if not rail:
        raise ValueError("No suitable payment rail available for this amount")

    # Create transaction
    txn = Transaction(
        sender_user_id=user_id,
        receiver_merchant_id=merchant_id,
        amount=amount,
        currency="USD",
        rail=rail,
        status="processing",
        idempotency_key=idempotency_key,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)

    log_event(db, "consumer_payment.initiated", "consumer_payment_service", txn.id, {
        "rail": rail, "amount": str(amount), "user_id": user_id,
    })

    # Call mock bank
    transfer_request = TransferRequest(
        sender_account_id=user_id,
        receiver_account_id=merchant_id,
        amount=amount,
        rail=rail,
        idempotency_key=idempotency_key,
    )

    result = mock_bank_service.initiate_transfer(transfer_request)

    # Update transaction with result
    txn.reference_id = result.reference_id
    txn.status = result.status
    txn.failure_reason = result.failure_reason
    db.commit()

    # Generate AI description
    generated_desc = description_service.generate_description(
        merchant.name, float(amount), rail, description
    )
    txn.description = generated_desc
    db.commit()

    # If completed, update ledger entries
    if result.status == "completed":
        # 1.25% discount for FedNow/RTP rails
        if rail in ("fednow", "rtp"):
            settled_amount = (amount * Decimal("0.9875")).quantize(Decimal("0.01"))
        else:
            settled_amount = amount
        txn.amount = settled_amount
        db.commit()
        wallet_debit(db, user_id, settled_amount, txn.id, generated_desc)
        record_credit(db, merchant_id, settled_amount, txn.id, f"Payment from consumer {user_id}")
        db.commit()
        log_event(db, "consumer_payment.completed", "consumer_payment_service", txn.id)
    elif result.status == "failed":
        log_event(db, "consumer_payment.failed", "consumer_payment_service", txn.id, {
            "reason": result.failure_reason,
        })

    # Send notification to consumer user
    notification_service.notify_transaction(
        db, user_id, txn.id, txn.status,
        float(txn.amount), merchant.name, rail, txn.description,
    )

    return {
        "transaction_id": txn.id,
        "status": txn.status,
        "reference_id": txn.reference_id,
        "failure_reason": txn.failure_reason,
    }
