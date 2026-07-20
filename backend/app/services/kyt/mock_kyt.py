"""Deterministic mock KYT provider.

Addresses containing a block/review marker are flagged; everything else passes.
This lets tests exercise the sanctions gate without a real analytics vendor.
"""
from decimal import Decimal

from app.services.kyt.interface import KytProviderInterface
from app.services.kyt.schemas import ScreeningOutcome, ScreeningResult

BLOCK_MARKERS = ("blocked", "ofac", "sanction", "0xbad")
REVIEW_MARKERS = ("review", "0xrisk")


class MockKytProvider(KytProviderInterface):
    def screen_address(self, address: str, asset_code: str, network: str) -> ScreeningOutcome:
        a = (address or "").lower()
        if any(m in a for m in BLOCK_MARKERS):
            return ScreeningOutcome(result=ScreeningResult.BLOCK, risk_score=Decimal("95"),
                                    provider="mock", raw={"address": address, "reason": "denylist"})
        if any(m in a for m in REVIEW_MARKERS):
            return ScreeningOutcome(result=ScreeningResult.REVIEW, risk_score=Decimal("60"),
                                    provider="mock", raw={"address": address})
        return ScreeningOutcome(result=ScreeningResult.PASS, risk_score=Decimal("2"),
                                provider="mock", raw={"address": address})


mock_kyt_provider = MockKytProvider()
