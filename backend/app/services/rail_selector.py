from decimal import Decimal
from typing import Optional

from app.services.bank.mock_bank import RAIL_LIMITS

# Priority order: FedNow → RTP → ACH → Card
RAIL_PRIORITY = ["fednow", "rtp", "ach", "card"]


def select_rail(
    amount: Decimal,
    supported_rails: str,
    preferred_rail: Optional[str] = None,
) -> Optional[str]:
    available = [r.strip() for r in supported_rails.split(",")]

    # If a preferred rail is specified and valid, try it first
    if preferred_rail and preferred_rail in available:
        limit = RAIL_LIMITS.get(preferred_rail)
        if limit and amount <= limit:
            return preferred_rail

    # Fall through priority order
    for rail in RAIL_PRIORITY:
        if rail not in available:
            continue
        limit = RAIL_LIMITS.get(rail)
        if limit and amount <= limit:
            return rail

    return None
