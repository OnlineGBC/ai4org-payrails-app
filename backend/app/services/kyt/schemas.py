from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class ScreeningResult(str, Enum):
    PASS = "pass"
    REVIEW = "review"
    BLOCK = "block"


class ScreeningOutcome(BaseModel):
    result: ScreeningResult
    risk_score: Decimal
    provider: str
    raw: Optional[dict] = None
