import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, func
from app.database import Base


class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False, index=True)
    bank_name = Column(String, nullable=True)
    routing_number = Column(String, nullable=False)
    encrypted_account_number = Column(String, nullable=False)
    account_type = Column(String, default="checking")  # checking, savings
    verification_status = Column(String, default="pending")  # pending, micro_deposit_sent, verified, failed
    micro_deposit_amount_1 = Column(String, nullable=True)
    micro_deposit_amount_2 = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
