from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models.transaction import Transaction
from app.services.ledger_service import record_debit, record_credit
from app.services.event_service import log_event

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class BankWebhookPayload(BaseModel):
    reference_id: str
    status: str  # completed, failed
    failure_reason: Optional[str] = None


@router.post("/bank")
def receive_bank_webhook(
    payload: BankWebhookPayload,
    db: Session = Depends(get_db),
):
    txn = db.query(Transaction).filter(Transaction.reference_id == payload.reference_id).first()
    if not txn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    if txn.status in ("completed", "failed", "cancelled"):
        return {"status": "already_processed"}

    txn.status = payload.status
    txn.failure_reason = payload.failure_reason
    db.commit()

    if payload.status == "completed":
        from decimal import Decimal
        amount = Decimal(str(txn.amount))
        record_debit(db, txn.sender_merchant_id, amount, txn.id, "Payment sent (webhook)")
        record_credit(db, txn.receiver_merchant_id, amount, txn.id, "Payment received (webhook)")

    log_event(db, f"webhook.bank.{payload.status}", "webhooks_router", txn.id, {
        "reference_id": payload.reference_id,
    })

    return {"status": "processed"}
