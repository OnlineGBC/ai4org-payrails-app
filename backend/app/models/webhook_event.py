import uuid
from sqlalchemy import Column, String, DateTime, func
from app.database import Base


class WebhookEvent(Base):
    """Idempotency ledger for inbound partner webhooks (keyed by event_id)."""

    __tablename__ = "webhook_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    provider = Column(String, nullable=False)              # 'zerohash'
    event_id = Column(String, nullable=False, unique=True, index=True)
    event_type = Column(String, nullable=True)
    received_at = Column(DateTime, server_default=func.now())
