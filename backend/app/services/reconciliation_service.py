"""Reconciliation between the internal ledger and the partner/on-chain balance.

The core audit artifact for stablecoins: drift between what PayRails' ledger says
an owner (consumer wallet or merchant) holds and what the custodial partner
reports must be zero.
"""
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.services.ledger_service import get_balance
from app.services.stablecoin import get_stablecoin_provider
from app.services.wallet_service import get_wallet_balance


def reconcile_owner(db: Session, asset_code: str, partner_account_id: str,
                    user_id: Optional[str] = None, merchant_id: Optional[str] = None) -> dict:
    """Compare an owner's internal balance vs the partner-reported balance."""
    provider = get_stablecoin_provider()
    internal = get_balance(db, merchant_id, asset_code) if merchant_id \
        else get_wallet_balance(db, user_id, asset_code)
    external = Decimal(str(provider.get_balance(partner_account_id, asset_code)))
    drift = internal - external
    return {
        "user_id": user_id,
        "merchant_id": merchant_id,
        "asset_code": asset_code,
        "internal_balance": internal,
        "external_balance": external,
        "drift": drift,
        "reconciled": drift == 0,
    }


def reconcile_wallet(db: Session, user_id: str, asset_code: str, partner_account_id: str) -> dict:
    """Backward-compatible consumer-wallet reconciliation."""
    return reconcile_owner(db, asset_code, partner_account_id, user_id=user_id)
