import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint, func
from app.database import Base


class CryptoAccount(Base):
    """Custodial crypto account / deposit address issued by the regulated partner."""

    __tablename__ = "crypto_accounts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=True)
    partner = Column(String, nullable=False)             # 'zerohash'
    partner_account_id = Column(String, nullable=False)
    asset_code = Column(String, ForeignKey("assets.code"), nullable=False)
    network = Column(String, nullable=False)
    deposit_address = Column(String, nullable=True)
    status = Column(String, nullable=False, default="pending")  # pending | active | frozen
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint(
            "partner", "partner_account_id", "asset_code", "network",
            name="uq_crypto_account",
        ),
    )
