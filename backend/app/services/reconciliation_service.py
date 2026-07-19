"""Reconciliation between the internal ledger and the partner/on-chain balance.

The core audit artifact for stablecoins: drift between what PayRails' ledger says
a user holds and what the custodial partner reports must be zero. A background job
(step 4) will run this on a schedule; here it is a pure, callable comparison.
"""
from decimal import Decimal

from sqlalchemy.orm import Session

from app.services.stablecoin import get_stablecoin_provider
from app.services.wallet_service import get_wallet_balance


def reconcile_wallet(db: Session, user_id: str, asset_code: str, partner_account_id: str) -> dict:
    """Compare internal wallet balance vs the partner-reported balance for an asset."""
    provider = get_stablecoin_provider()
    internal = get_wallet_balance(db, user_id, asset_code)
    external = Decimal(str(provider.get_balance(partner_account_id, asset_code)))
    drift = internal - external
    return {
        "user_id": user_id,
        "asset_code": asset_code,
        "internal_balance": internal,
        "external_balance": external,
        "drift": drift,
        "reconciled": drift == 0,
    }
