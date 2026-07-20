"""Sanctions / KYT screening: run a screen and persist it as audit evidence."""
import json
from typing import Optional

from sqlalchemy.orm import Session

from app.models.sanctions_screening import SanctionsScreening
from app.services.kyt import get_kyt_provider


class ScreeningBlockedError(PermissionError):
    """Raised when an address is screened as blocked (sanctions/KYT hit)."""


def screen_address(
    db: Session,
    address: str,
    asset_code: str,
    network: str,
    transaction_id: Optional[str] = None,
) -> SanctionsScreening:
    """Screen an address via the KYT provider and record the result."""
    outcome = get_kyt_provider().screen_address(address, asset_code, network)
    row = SanctionsScreening(
        transaction_id=transaction_id,
        address=address,
        provider=outcome.provider,
        result=outcome.result.value,
        risk_score=outcome.risk_score,
        raw_payload=json.dumps(outcome.raw) if outcome.raw else None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
