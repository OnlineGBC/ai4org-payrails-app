import uuid
from sqlalchemy import Column, String, SmallInteger, Boolean, ForeignKey, UniqueConstraint
from app.database import Base


class AssetNetwork(Base):
    """Chains on which a given stablecoin is supported, with confirmation policy."""

    __tablename__ = "asset_networks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_code = Column(String, ForeignKey("assets.code"), nullable=False)
    network = Column(String, nullable=False)             # 'ethereum', 'solana', 'bnb'
    contract_address = Column(String, nullable=True)
    min_confirmations = Column(SmallInteger, nullable=False, default=12)
    is_active = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint("asset_code", "network", name="uq_asset_network"),
    )
