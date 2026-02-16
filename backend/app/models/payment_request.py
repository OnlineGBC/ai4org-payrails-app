import uuid
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, func
from app.database import Base


class PaymentRequest(Base):
    __tablename__ = "payment_requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, default="USD")
    description = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, completed, expired, cancelled
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
