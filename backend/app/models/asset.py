from sqlalchemy import Column, String, SmallInteger, Boolean
from app.database import Base


class Asset(Base):
    """Reference table of supported assets (fiat + stablecoins).

    decimals drives base-unit conversion: 2 for USD, 6 for USDC/USD1.
    """

    __tablename__ = "assets"

    code = Column(String, primary_key=True)          # 'USD', 'USDC', 'USD1'
    asset_type = Column(String, nullable=False)      # 'fiat' | 'stablecoin'
    decimals = Column(SmallInteger, nullable=False)  # 2 for USD, 6 for stablecoins
    display_name = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
