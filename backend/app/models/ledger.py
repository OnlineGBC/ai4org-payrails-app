import uuid
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, func
from app.database import Base


class Ledger(Base):
    __tablename__ = "ledger"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=True)
    entry_type = Column(String, nullable=False)  # debit, credit
    # Legacy USD-only Decimal columns (nullable: stablecoin entries use base units).
    amount = Column(Numeric(12, 2), nullable=True)
    balance_after = Column(Numeric(12, 2), nullable=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # --- multi-asset / stablecoin scaffolding (not yet wired into ledger logic) ---
    # Balances are per (owner, asset_code); base-unit columns store integer minor
    # units (amount x 10^asset.decimals) to avoid mixing 2- and 6-decimal precision.
    asset_code = Column(
        String, ForeignKey("assets.code"),
        nullable=False, default="USD", server_default="USD",
    )
    amount_base_units = Column(Numeric(38, 0), nullable=True)
    balance_after_base_units = Column(Numeric(38, 0), nullable=True)
