"""Stablecoin orchestration (step 3 business logic).

Wires the regulated-partner provider (mock today) to the multi-asset ledger:
KYC gating, custodial-account provisioning, on/off-ramp, send, deposit crediting,
and an idempotent settlement state machine. No HTTP endpoints yet (step 6) and no
async workers yet (step 4) -- callers invoke these synchronously; the mock
provider settles instantly to CONFIRMED.
"""
import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.kyc_record import KycRecord
from app.models.crypto_account import CryptoAccount
from app.models.ledger import Ledger
from app.services.stablecoin import get_stablecoin_provider
from app.services.stablecoin.schemas import KycStatus, OnchainStatus
from app.services.units import to_base_units, from_base_units
from app.services.wallet_service import wallet_credit, wallet_debit


class KycRequiredError(PermissionError):
    """Raised when a user attempts a crypto action without approved KYC."""


def _new_key() -> str:
    return uuid.uuid4().hex


# --------------------------------------------------------------------------- KYC

def ensure_kyc(db: Session, user_id: str, payload: Optional[dict] = None) -> KycRecord:
    """Idempotently submit/refresh KYC for a user via the partner."""
    record = db.query(KycRecord).filter(KycRecord.user_id == user_id).first()
    if record and record.status == KycStatus.APPROVED.value:
        return record

    provider = get_stablecoin_provider()
    partner_kyc_id = (record.partner_kyc_id if record else None) or provider.submit_kyc(user_id, payload or {})
    status = provider.get_kyc_status(partner_kyc_id)

    if record is None:
        record = KycRecord(user_id=user_id, partner="mock", partner_kyc_id=partner_kyc_id, status=status.value)
        db.add(record)
    else:
        record.partner_kyc_id = partner_kyc_id
        record.status = status.value
    db.commit()
    db.refresh(record)
    return record


def require_kyc_approved(db: Session, user_id: str) -> None:
    record = db.query(KycRecord).filter(KycRecord.user_id == user_id).first()
    if not record or record.status != KycStatus.APPROVED.value:
        raise KycRequiredError("KYC not approved for user")


# ----------------------------------------------------------------- accounts

def ensure_crypto_account(db: Session, user_id: str, asset_code: str, network: str) -> CryptoAccount:
    account = db.query(CryptoAccount).filter(
        CryptoAccount.user_id == user_id,
        CryptoAccount.asset_code == asset_code,
        CryptoAccount.network == network,
    ).first()
    if account:
        return account

    provider = get_stablecoin_provider()
    provided = provider.create_account(user_id, asset_code, network)
    account = CryptoAccount(
        user_id=user_id, partner="mock",
        partner_account_id=provided.partner_account_id,
        asset_code=asset_code, network=network,
        deposit_address=provided.deposit_address, status="active",
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


# ------------------------------------------------------------- transactions

def _create_tx(
    db: Session, *, direction: str, asset_code: str, amount: Decimal, network: str,
    onchain_tx_hash: Optional[str], onchain_status: str, confirmations: int,
    partner_transfer_id: Optional[str], status: str,
    sender_user_id: Optional[str] = None, receiver_user_id: Optional[str] = None,
    description: Optional[str] = None,
) -> Transaction:
    tx = Transaction(
        sender_user_id=sender_user_id,
        receiver_user_id=receiver_user_id,
        amount=None,
        amount_base_units=to_base_units(amount, asset_code),
        currency=asset_code,
        asset_code=asset_code,
        status=status,
        idempotency_key=_new_key(),
        reference_id=partner_transfer_id,
        settlement_type="onchain",
        settlement_network=network,
        onchain_tx_hash=onchain_tx_hash,
        onchain_status=onchain_status,
        confirmations=confirmations,
        partner="mock",
        partner_transfer_id=partner_transfer_id,
        direction=direction,
        description=description,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def onramp(db: Session, user_id: str, usd_amount: Decimal, asset_code: str, network: str = "ethereum") -> Transaction:
    """Buy stablecoin with USD; credits the user's wallet in `asset_code`."""
    require_kyc_approved(db, user_id)
    provider = get_stablecoin_provider()
    quote = provider.quote_onramp(usd_amount, asset_code)
    result = provider.execute_onramp(quote.quote_id, _new_key())

    tx = _create_tx(
        db, direction="onramp", asset_code=asset_code, amount=quote.to_amount, network=network,
        onchain_tx_hash=result.onchain_tx_hash, onchain_status=result.status.value,
        confirmations=result.confirmations, partner_transfer_id=result.partner_transfer_id,
        status="processing", receiver_user_id=user_id,
        description=f"On-ramp {usd_amount} USD to {asset_code}",
    )
    return apply_settlement_update(db, tx, result.status, result.confirmations, result.onchain_tx_hash)


def offramp(db: Session, user_id: str, asset_code: str, amount: Decimal, network: str = "ethereum") -> Transaction:
    """Sell stablecoin for USD; debits the user's wallet in `asset_code`."""
    require_kyc_approved(db, user_id)
    provider = get_stablecoin_provider()

    debit = wallet_debit(db, user_id, amount, description=f"Off-ramp {amount} {asset_code}", asset_code=asset_code)
    quote = provider.quote_offramp(amount, asset_code)
    result = provider.execute_offramp(quote.quote_id, _new_key())

    if result.status == OnchainStatus.FAILED:
        wallet_credit(db, user_id, amount, description="Off-ramp reversal", asset_code=asset_code)
        status = "failed"
    else:
        status = "completed"

    tx = _create_tx(
        db, direction="offramp", asset_code=asset_code, amount=amount, network=network,
        onchain_tx_hash=result.onchain_tx_hash, onchain_status=result.status.value,
        confirmations=result.confirmations, partner_transfer_id=result.partner_transfer_id,
        status=status, sender_user_id=user_id,
        description=f"Off-ramp {amount} {asset_code} to USD",
    )
    debit.transaction_id = tx.id
    db.commit()
    return tx


def send_stablecoin(db: Session, user_id: str, to_address: str, asset_code: str, amount: Decimal, network: str = "ethereum") -> Transaction:
    """Send stablecoin on-chain to an external address; debits the user's wallet."""
    require_kyc_approved(db, user_id)
    account = ensure_crypto_account(db, user_id, asset_code, network)
    provider = get_stablecoin_provider()

    debit = wallet_debit(db, user_id, amount, description=f"Send {amount} {asset_code}", asset_code=asset_code)
    result = provider.transfer(account.partner_account_id, to_address, asset_code, network, amount, _new_key())

    if result.status == OnchainStatus.FAILED:
        wallet_credit(db, user_id, amount, description="Send reversal", asset_code=asset_code)
        status = "failed"
    else:
        status = "completed"

    tx = _create_tx(
        db, direction="send", asset_code=asset_code, amount=amount, network=network,
        onchain_tx_hash=result.onchain_tx_hash, onchain_status=result.status.value,
        confirmations=result.confirmations, partner_transfer_id=result.partner_transfer_id,
        status=status, sender_user_id=user_id,
        description=f"Send {amount} {asset_code} to {to_address}",
    )
    debit.transaction_id = tx.id
    db.commit()
    return tx


def credit_deposit(db: Session, user_id: str, asset_code: str, amount: Decimal, onchain_tx_hash: str, network: str = "ethereum") -> Transaction:
    """Credit an inbound on-chain deposit. Idempotent by onchain_tx_hash."""
    existing = db.query(Transaction).filter(Transaction.onchain_tx_hash == onchain_tx_hash).first()
    if existing:
        return existing

    tx = _create_tx(
        db, direction="deposit", asset_code=asset_code, amount=amount, network=network,
        onchain_tx_hash=onchain_tx_hash, onchain_status=OnchainStatus.CONFIRMED.value,
        confirmations=12, partner_transfer_id=None, status="processing",
        receiver_user_id=user_id, description=f"Deposit {amount} {asset_code}",
    )
    return apply_settlement_update(db, tx, OnchainStatus.CONFIRMED, 12, onchain_tx_hash)


# --------------------------------------------------------- settlement machine

def apply_settlement_update(
    db: Session, tx: Transaction, status: OnchainStatus,
    confirmations: int = 0, onchain_tx_hash: Optional[str] = None,
) -> Transaction:
    """Advance a transaction's on-chain state; credit inbound value once confirmed.

    Idempotent: crediting is guarded by the presence of a ledger entry for this
    transaction, so replays (e.g. duplicate webhooks in step 4) are safe.
    """
    tx.onchain_status = status.value
    tx.confirmations = confirmations
    if onchain_tx_hash:
        tx.onchain_tx_hash = onchain_tx_hash

    if status == OnchainStatus.CONFIRMED and tx.status != "completed":
        already = db.query(Ledger).filter(Ledger.transaction_id == tx.id).first()
        if tx.direction in ("onramp", "deposit") and tx.receiver_user_id and not already:
            amount = from_base_units(int(tx.amount_base_units or 0), tx.asset_code or "USD")
            wallet_credit(
                db, tx.receiver_user_id, amount, transaction_id=tx.id,
                description=tx.description, asset_code=tx.asset_code or "USD",
            )
        tx.status = "completed"

    db.commit()
    db.refresh(tx)
    return tx
