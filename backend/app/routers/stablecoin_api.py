"""User-facing stablecoin API.

Exposes the orchestration to authenticated consumer and merchant accounts: KYC,
custodial account/deposit address, on/off-ramp, send, per-asset balances, and
on-chain history. Balances belong to the merchant entity for merchant_admin
logins and to the consumer wallet for user logins; crypto actions are KYC-gated
in the service layer.
"""
from decimal import Decimal
from typing import Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.crypto_account import CryptoAccount
from app.models.kyc_record import KycRecord
from app.models.transaction import Transaction
from app.models.user import User
from app.services import stablecoin_service as sc
from app.services.chain_config import is_supported_network
from app.services.ledger_service import get_balance
from app.services.rate_limiter import rate_limiter
from app.services.screening_service import ScreeningBlockedError
from app.services.units import from_base_units
from app.services.wallet_service import get_wallet_balance

SUPPORTED_ASSETS = ("USDC", "USD1")


def rate_limit(request: Request, current_user: User = Depends(get_current_user)) -> None:
    """Per-user, per-route fixed-window rate limit (config-driven)."""
    if not settings.RATE_LIMIT_ENABLED:
        return
    key = f"{current_user.id}:{request.url.path}"
    if not rate_limiter.allow(
        key, settings.RATE_LIMIT_MAX_REQUESTS, settings.RATE_LIMIT_WINDOW_SECONDS
    ):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail="Rate limit exceeded")


router = APIRouter(prefix="/stablecoin", tags=["stablecoin"], dependencies=[Depends(rate_limit)])


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

def _require_stablecoin_account(user: User) -> None:
    if user.role not in ("user", "merchant_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Stablecoin access requires a consumer or merchant account")


def _owner(user: User) -> Tuple[str, Optional[str]]:
    """Returns (acting_user_id, owner_merchant_id). merchant_id is set for
    merchant_admin logins (balance on the merchant entity) and None for consumers."""
    _require_stablecoin_account(user)
    if user.role == "merchant_admin":
        if not user.merchant_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Merchant account not linked")
        return user.id, user.merchant_id
    return user.id, None


def _owner_balance(db: Session, asset_code: str, user_id: str, merchant_id: Optional[str]) -> Decimal:
    return get_balance(db, merchant_id, asset_code) if merchant_id \
        else get_wallet_balance(db, user_id, asset_code)


def _validate_asset(asset_code: str) -> None:
    if asset_code not in SUPPORTED_ASSETS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported asset: {asset_code}")


def _validate_network(network: str) -> None:
    if not is_supported_network(network):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported network: {network}")


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
    _require_stablecoin_account(current_user)
    record = sc.ensure_kyc(db, current_user.id, payload.model_dump())
    return {"user_id": current_user.id, "status": record.status}


@router.get("/kyc")
def get_kyc(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _require_stablecoin_account(current_user)
    record = db.query(KycRecord).filter(KycRecord.user_id == current_user.id).first()
    return {"user_id": current_user.id, "status": record.status if record else "not_started"}


# --------------------------------------------------------------- accounts

@router.post("/accounts")
def create_account(payload: AccountRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    uid, mid = _owner(current_user)
    _validate_asset(payload.asset_code)
    _validate_network(payload.network)
    account = _guard(lambda: sc.ensure_crypto_account(db, uid, payload.asset_code, payload.network, merchant_id=mid))
    return {
        "id": account.id,
        "asset_code": account.asset_code,
        "network": account.network,
        "deposit_address": account.deposit_address,
        "status": account.status,
    }


@router.get("/accounts")
def list_accounts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    uid, mid = _owner(current_user)
    q = db.query(CryptoAccount).filter(CryptoAccount.merchant_id == mid) if mid \
        else db.query(CryptoAccount).filter(CryptoAccount.user_id == uid, CryptoAccount.merchant_id.is_(None))
    return [
        {"id": a.id, "asset_code": a.asset_code, "network": a.network,
         "deposit_address": a.deposit_address, "status": a.status}
        for a in q.all()
    ]


# --------------------------------------------------------------- balances

@router.get("/balances")
def balances(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    uid, mid = _owner(current_user)
    return {
        "user_id": uid,
        "merchant_id": mid,
        "balances": [
            {"asset_code": asset, "balance": str(_owner_balance(db, asset, uid, mid))}
            for asset in SUPPORTED_ASSETS
        ],
    }


# --------------------------------------------------------------- ramps / send

@router.post("/onramp")
def onramp(payload: OnrampRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    uid, mid = _owner(current_user)
    _validate_asset(payload.asset_code)
    _validate_network(payload.network)
    _require_positive(payload.usd_amount)
    tx = _guard(lambda: sc.onramp(db, uid, payload.usd_amount, payload.asset_code, payload.network, merchant_id=mid))
    return _tx_out(tx)


@router.post("/offramp")
def offramp(payload: OfframpRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    uid, mid = _owner(current_user)
    _validate_asset(payload.asset_code)
    _validate_network(payload.network)
    _require_positive(payload.amount)
    tx = _guard(lambda: sc.offramp(db, uid, payload.asset_code, payload.amount, payload.network, merchant_id=mid))
    return _tx_out(tx)


@router.post("/send")
def send(payload: SendRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    uid, mid = _owner(current_user)
    _validate_asset(payload.asset_code)
    _validate_network(payload.network)
    _require_positive(payload.amount)
    if not payload.to_address:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Destination address required")
    tx = _guard(lambda: sc.send_stablecoin(db, uid, payload.to_address, payload.asset_code,
                                           payload.amount, payload.network, merchant_id=mid))
    return _tx_out(tx)


# --------------------------------------------------------------- history

@router.get("/transactions")
def transactions(asset_code: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    uid, mid = _owner(current_user)
    q = db.query(Transaction).filter(Transaction.settlement_type == "onchain")
    if mid:
        q = q.filter((Transaction.sender_merchant_id == mid) | (Transaction.receiver_merchant_id == mid))
    else:
        q = q.filter((Transaction.sender_user_id == uid) | (Transaction.receiver_user_id == uid))
    if asset_code:
        q = q.filter(Transaction.asset_code == asset_code)
    txns = q.order_by(Transaction.created_at.desc()).all()
    return [_tx_out(tx) for tx in txns]
