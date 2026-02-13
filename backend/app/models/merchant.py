import uuid
from sqlalchemy import Column, String, DateTime, func
from app.database import Base


class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    ein = Column(String, unique=True, nullable=True)
    contact_email = Column(String, nullable=False)
    contact_phone = Column(String, nullable=True)
    onboarding_status = Column(String, default="pending")  # pending, active, suspended
    kyb_status = Column(String, default="not_submitted")  # not_submitted, pending, approved, rejected
    sponsor_bank_id = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
