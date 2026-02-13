import uuid
from sqlalchemy import Column, String, Numeric, DateTime, Boolean, func
from app.database import Base


class BankConfig(Base):
    __tablename__ = "bank_configs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    bank_name = Column(String, unique=True, nullable=False)
    supported_rails = Column(String, nullable=False)  # comma-separated: fednow,rtp,ach,card
    fednow_limit = Column(Numeric(12, 2), default=500000)
    rtp_limit = Column(Numeric(12, 2), default=1000000)
    ach_limit = Column(Numeric(12, 2), default=10000000)
    is_active = Column(Boolean, default=True)
    oauth_client_id = Column(String, nullable=True)
    oauth_client_secret = Column(String, nullable=True)
    api_base_url = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
