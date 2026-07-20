"""Money precision helpers.

Monetary values are converted to integer BASE UNITS (amount x 10^decimals) for
exact, asset-aware storage/arithmetic. Each asset uses its own decimals, so USD
stays at 2-decimal (cent) precision and only native 6-decimal coins use 10^6 --
USD is never widened to 6 decimals.
"""
from decimal import Decimal, ROUND_HALF_UP

# Kept in sync with the seeded `assets` table. DB is the source of truth in prod;
# this map avoids a query on the hot path for the known set.
ASSET_DECIMALS = {"USD": 2, "USDC": 6, "USD1": 6}
DEFAULT_DECIMALS = 6


def decimals_for(asset_code: str) -> int:
    return ASSET_DECIMALS.get(asset_code, DEFAULT_DECIMALS)


def to_base_units(amount, asset_code: str) -> int:
    """Decimal amount -> integer base units (rounded to the asset's precision)."""
    d = decimals_for(asset_code)
    scaled = Decimal(str(amount)).scaleb(d)
    return int(scaled.to_integral_value(rounding=ROUND_HALF_UP))


def from_base_units(units, asset_code: str) -> Decimal:
    """Integer base units -> Decimal amount at the asset's precision."""
    d = decimals_for(asset_code)
    return Decimal(int(units)).scaleb(-d)
