"""Inbound partner (stablecoin) webhook receiver.

Mirrors /webhooks/bank but for the regulated stablecoin partner. Verifies the
signature via the provider, dedupes by event_id (webhook_events), and dispatches
to the service layer. Public endpoint, protected by signature verification.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.webhook_event import WebhookEvent
from app.services.event_service import log_event
from app.services.stablecoin import get_stablecoin_provider
from app.services.stablecoin_service import handle_partner_event
from app.services.webhook_security import verify_hmac

router = APIRouter(prefix="/webhooks", tags=["stablecoin-webhooks"])


def _verify_signature(request: Request, raw_body: bytes) -> bool:
    """Real HMAC verification when a webhook secret is configured; otherwise
    fall back to the provider check (mock in dev/tests)."""
    secret = settings.STABLECOIN_WEBHOOK_SECRET
    if secret:
        signature = request.headers.get("x-signature", "")
        return verify_hmac(secret, raw_body, signature)
    return get_stablecoin_provider().verify_webhook(dict(request.headers), raw_body)


@router.post("/stablecoin")
async def receive_stablecoin_webhook(request: Request, db: Session = Depends(get_db)):
    raw_body = await request.body()
    provider = get_stablecoin_provider()

    if not _verify_signature(request, raw_body):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")

    event = provider.parse_webhook_event(raw_body)
    event_id = event.get("event_id")
    event_type = event.get("type")
    if not event_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing event_id")

    # Idempotency: skip if this event_id was already recorded.
    if db.query(WebhookEvent).filter(WebhookEvent.event_id == event_id).first():
        return {"status": "already_processed"}

    outcome = handle_partner_event(db, event)

    try:
        db.add(WebhookEvent(provider="mock", event_id=event_id, event_type=event_type))
        db.commit()
    except IntegrityError:
        # Concurrent delivery recorded it first; safe to treat as processed.
        db.rollback()
        return {"status": "already_processed"}

    log_event(db, f"webhook.stablecoin.{event_type}", "stablecoin_webhooks", event_id, {"outcome": outcome})
    return {"status": "processed", "outcome": outcome}
