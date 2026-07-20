"""User-facing stablecoin API (step 6 backend).

Exposes the step-3 orchestration to authenticated consumer accounts: KYC,
custodial account/deposit address, on/off-ramp, send, per-asset balances, and
on-chain history. Consumer-only (role 'user'); crypto actions are KYC-gated in
the service layer.
"""
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.crypto_account import CryptoAccount
from app.models.kyc_record import KycRecord
from app.models.transaction import Transaction
from app.models.user import User
from app.services import stablecoin_service as sc
from app.services.screening_service import ScreeningBlockedError
from app.services.units import from_base_units
from app.services.wallet_service import get_wallet_balance

router = APIRouter(prefix="/stablecoin", tags=["stablecoin"])

SUPPORTED_ASSETS = ("USDC", "USD1")
SUPPORTED_NETWORKS = {"ethereum", "solana", "bnb"}


# --------------------------------------------------------------- requests

class KycRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    country: Optional[str] = None


class AccountRequest(BaseModel):
    asset_code: str
    network: str = "ethereum"


class OnrampRequest(BaseModel):
    usd_amount: Decimal
    asset_code: str
    network: str = "ethereum"


class OfframpRequest(BaseModel):
    amount: Decimal
    asset_code: str
    network: str = "ethereum"


class SendRequest(BaseModel):
    to_address: str
    amount: Decimal
    asset_code: str
    network: str = "ethereum"


# --------------------------------------------------------------- helpers

def _require_consumer(user: User) -> None:
    if user.role != "user":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Consumer account required")


def _validate_asset(asset_code: str) -> None:
    if asset_code not in SUPPORTED_ASSETS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Unsupported asset: {asset_code}")


def _validate_network(network: str) -> None:
    if network not in SUPPORTED_NETWORKS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Unsupported network: {network}")


def _require_positive(amount: Decimal) -> None:
    if amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be positive")


def _tx_out(tx: Transaction) -> dict:
    amount = (Decimal(str(tx.amount)) if tx.amount is not None
              else from_base_units(int(tx.amount_base_units or 0), tx.asset_code or "USD"))
    return {
        "id": tx.id,
        "direction": tx.direction,
        "asset_code": tx.asset_code,
        "amount": str(amount),
        "status": tx.status,
        "onchain_status": tx.onchain_status,
        "onchain_tx_hash": tx.onchain_tx_hash,
        "network": tx.settlement_network,
        "partner_transfer_id": tx.partner_transfer_id,
        "created_at": tx.created_at.isoformat() if tx.created_at else None,
    }


def _guard(fn):
    """Translate service-layer exceptions into HTTP errors."""
    try:
        return fn()
    except sc.KycRequiredError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="KYC not approved")
    except ScreeningBlockedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# --------------------------------------------------------------- KYC

@router.post("/kyc")
def submit_kyc(payload: KycRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _require_consumer(current_user)
    record = sc.ensure_kyc(db, current_user.id, payload.model_dump())
    return {"user_id": current_user.id, "status": record.status}


@router.get("/kyc")
def get_kyc(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _require_consumer(current_user)
    record = db.query(KycRecord).filter(KycRecord.user_id == current_user.id).first()
    return {"user_id": current_user.id, "status": record.status if record else "not_started"}


# --------------------------------------------------------------- accounts

@router.post("/accounts")
def create_account(payload: AccountRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _require_consumer(current_user)
    _validate_asset(payload.asset_code)
    _validate_network(payload.network)
    account = _guard(lambda: sc.ensure_crypto_account(db, current_user.id, payload.asset_code, payload.network))
    return {
        "id": account.id,
        "asset_code": account.asset_code,
        "network": account.network,
        "deposit_address": account.deposit_address,
        "status": account.status,
    }


@router.get("/accounts")
def list_accounts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _require_consumer(current_user)
    accounts = db.query(CryptoAccount).filter(CryptoAccount.user_id == current_user.id).all()
    return [
        {"id": a.id, "asset_code": a.asset_code, "network": a.network,
         "deposit_address": a.deposit_address, "status": a.status}
        for a in accounts
    ]


# --------------------------------------------------------------- balances

@router.get("/balances")
def balances(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _require_consumer(current_user)
    return {
        "user_id": current_user.id,
        "balances": [
            {"asset_code": asset, "balance": str(get_wallet_balance(db, current_user.id, asset))}
            for asset in SUPPORTED_ASSETS
        ],
    }


# --------------------------------------------------------------- ramps / send

@router.post("/onramp")
def onramp(payload: OnrampRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _require_consumer(current_user)
    _validate_asset(payload.asset_code)
    _validate_network(payload.network)
    _require_positive(payload.usd_amount)
    tx = _guard(lambda: sc.onramp(db, current_user.id, payload.usd_amount, payload.asset_code, payload.network))
    return _tx_out(tx)


@router.post("/offramp")
def offramp(payload: OfframpRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _require_consumer(current_user)
    _validate_asset(payload.asset_code)
    _validate_network(payload.network)
    _require_positive(payload.amount)
    tx = _guard(lambda: sc.offramp(db, current_user.id, payload.asset_code, payload.amount, payload.network))
    return _tx_out(tx)


@router.post("/send")
def send(payload: SendRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _require_consumer(current_user)
    _validate_asset(payload.asset_code)
    _validate_network(payload.network)
    _require_positive(payload.amount)
    if not payload.to_address:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Destination address required")
    tx = _guard(lambda: sc.send_stablecoin(db, current_user.id, payload.to_address, payload.asset_code, payload.amount, payload.network))
    return _tx_out(tx)


# --------------------------------------------------------------- history

@router.get("/transactions")
def transactions(asset_code: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _require_consumer(current_user)
    q = db.query(Transaction).filter(
        Transaction.settlement_type == "onchain",
        (Transaction.sender_user_id == current_user.id) | (Transaction.receiver_user_id == current_user.id),
    )
    if asset_code:
        q = q.filter(Transaction.asset_code == asset_code)
    txns = q.order_by(Transaction.created_at.desc()).all()
    return [_tx_out(tx) for tx in txns]
