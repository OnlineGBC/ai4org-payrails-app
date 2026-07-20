"""Chainalysis KYT provider (STUB).

Scaffold only. Wiring the real Chainalysis (or TRM / Elliptic) API -- address
risk lookup, category/exposure mapping to pass/review/block, retries -- is later
work. Config to add: KYT_API_KEY, KYT_BASE_URL.
"""
from app.services.kyt.interface import KytProviderInterface
from app.services.kyt.schemas import ScreeningOutcome

_PENDING = "Chainalysis KYT integration pending"


class ChainalysisKytProvider(KytProviderInterface):
    def __init__(self, api_key: str = "", base_url: str = "") -> None:
        self.api_key = api_key
        self.base_url = base_url

    def screen_address(self, address: str, asset_code: str, network: str) -> ScreeningOutcome:
        raise NotImplementedError(_PENDING)
