import uuid
from sqlalchemy import Column, String, Numeric, DateTime, func
from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_merchant_id = Column(String, nullable=False, index=True)
    receiver_merchant_id = Column(String, nullable=False, index=True)
    sender_bank_account_id = Column(String, nullable=True)
    receiver_bank_account_id = Column(String, nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, default="USD")
    rail = Column(String, nullable=True)  # fednow, rtp, ach, card
    status = Column(String, default="pending")  # pending, processing, completed, failed, cancelled
    idempotency_key = Column(String, unique=True, nullable=False, index=True)
    reference_id = Column(String, nullable=True)
    failure_reason = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
