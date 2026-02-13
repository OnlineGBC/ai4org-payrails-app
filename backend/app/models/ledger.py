import uuid
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, func
from app.database import Base


class Ledger(Base):
    __tablename__ = "ledger"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False, index=True)
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=True)
    entry_type = Column(String, nullable=False)  # debit, credit
    amount = Column(Numeric(12, 2), nullable=False)
    balance_after = Column(Numeric(12, 2), nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
