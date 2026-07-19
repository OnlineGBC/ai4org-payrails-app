import uuid
from sqlalchemy import Column, String, Text, Numeric, DateTime, ForeignKey, func
from app.database import Base


class SanctionsScreening(Base):
    """KYT / sanctions screening result retained as audit evidence."""

    __tablename__ = "sanctions_screening"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=True, index=True)
    address = Column(String, nullable=True)
    provider = Column(String, nullable=False)            # 'chainalysis' | 'trm' | 'elliptic'
    result = Column(String, nullable=False)              # 'pass' | 'review' | 'block'
    risk_score = Column(Numeric(6, 2), nullable=True)
    raw_payload = Column(Text, nullable=True)
    screened_at = Column(DateTime, server_default=func.now())
