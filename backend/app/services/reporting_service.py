"""Compliance reporting queries over the on-chain audit trail.

Read-only exports that feed regulatory reporting (SAR/CTR/1099-DA, MTL call
reports). USD stablecoins are treated ~1:1 with USD for thresholding.
"""
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.sanctions_screening import SanctionsScreening
from app.models.transaction import Transaction
from app.services.units import from_base_units

CTR_THRESHOLD = Decimal("10000")  # USD-equivalent


def _tx_amount(tx: Transaction) -> Decimal:
    if tx.amount is not None:
        return Decimal(str(tx.amount))
    return from_base_units(int(tx.amount_base_units or 0), tx.asset_code or "USD")


def onchain_audit_trail(db: Session, asset_code: Optional[str] = None) -> list:
    """Every on-chain transaction with its ledger-linking identifiers."""
    q = db.query(Transaction).filter(Transaction.settlement_type == "onchain")
    if asset_code:
        q = q.filter(Transaction.asset_code == asset_code)
    rows = []
    for tx in q.order_by(Transaction.created_at).all():
        rows.append({
            "transaction_id": tx.id,
            "direction": tx.direction,
            "asset_code": tx.asset_code,
            "amount": _tx_amount(tx),
            "network": tx.settlement_network,
            "onchain_tx_hash": tx.onchain_tx_hash,
            "partner_transfer_id": tx.partner_transfer_id,
            "onchain_status": tx.onchain_status,
            "status": tx.status,
            "sender_user_id": tx.sender_user_id,
            "receiver_user_id": tx.receiver_user_id,
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
        })
    return rows


def ctr_report(db: Session, threshold: Decimal = CTR_THRESHOLD) -> list:
    """On-chain transactions at/above the CTR reporting threshold."""
    return [r for r in onchain_audit_trail(db) if r["amount"] >= threshold]


def screening_report(db: Session, include_pass: bool = False) -> list:
    """Sanctions/KYT screening results (review/block by default)."""
    q = db.query(SanctionsScreening)
    if not include_pass:
        q = q.filter(SanctionsScreening.result != "pass")
    return [{
        "id": s.id,
        "transaction_id": s.transaction_id,
        "address": s.address,
        "provider": s.provider,
        "result": s.result,
        "risk_score": Decimal(str(s.risk_score)) if s.risk_score is not None else None,
    } for s in q.order_by(SanctionsScreening.screened_at).all()]
