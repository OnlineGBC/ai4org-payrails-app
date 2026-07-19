import uuid
from sqlalchemy import Column, String, Numeric, Integer, DateTime, ForeignKey, func
from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_merchant_id = Column(String, nullable=True, index=True)
    sender_user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    receiver_merchant_id = Column(String, nullable=True, index=True)
    receiver_user_id = Column(String, nullable=True, index=True)
    sender_bank_account_id = Column(String, nullable=True)
    receiver_bank_account_id = Column(String, nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, default="USD")
    rail = Column(String, nullable=True)  # fednow, rtp, ach, card
    status = Column(String, default="pending")  # pending, processing, completed, failed, cancelled
    idempotency_key = Column(String, unique=True, nullable=False, index=True)
    reference_id = Column(String, nullable=True)
    failure_reason = Column(String, nullable=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # --- stablecoin / on-chain settlement scaffolding (not yet wired into logic) ---
    asset_code = Column(
        String, ForeignKey("assets.code"),
        nullable=False, default="USD", server_default="USD",
    )
    amount_base_units = Column(Numeric(38, 0), nullable=True)
    settlement_type = Column(
        String, nullable=False, default="offchain", server_default="offchain",
    )  # offchain | onchain
    settlement_network = Column(String, nullable=True)   # ethereum | solana | bnb
    onchain_tx_hash = Column(String, unique=True, nullable=True)
    onchain_status = Column(String, nullable=True)       # submitted|confirming|confirmed|failed|reorged
    confirmations = Column(Integer, nullable=True, default=0, server_default="0")
    partner = Column(String, nullable=True)              # 'zerohash'
    partner_transfer_id = Column(String, nullable=True, index=True)
    direction = Column(String, nullable=True)            # onramp|offramp|send|deposit|withdrawal
