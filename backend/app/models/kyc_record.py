import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func
from app.database import Base


class KycRecord(Base):
    """Partner-driven KYC status for a user. Gates all crypto features."""

    __tablename__ = "kyc_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    partner = Column(String, nullable=False)
    partner_kyc_id = Column(String, nullable=True)
    status = Column(String, nullable=False, default="not_started")  # not_started | pending | approved | rejected
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
