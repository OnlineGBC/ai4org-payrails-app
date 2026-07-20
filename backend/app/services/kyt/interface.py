from abc import ABC, abstractmethod

from app.services.kyt.schemas import ScreeningOutcome


class KytProviderInterface(ABC):
    """Contract for a blockchain-analytics / sanctions-screening provider."""

    @abstractmethod
    def screen_address(self, address: str, asset_code: str, network: str) -> ScreeningOutcome:
        ...
