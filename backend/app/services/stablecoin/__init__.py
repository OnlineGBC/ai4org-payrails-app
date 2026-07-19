"""Stablecoin provider integration layer.

Mirrors app/services/bank/ (interface + schemas + mock) so business logic stays
provider-agnostic. A ZeroHashProvider implements the interface for production;
MockStablecoinProvider backs dev/tests. USDC and USD1 ride the same interface.
"""

from app.services.stablecoin.interface import StablecoinProviderInterface
from app.services.stablecoin.mock_provider import (
    MockStablecoinProvider,
    mock_stablecoin_provider,
)

__all__ = [
    "StablecoinProviderInterface",
    "MockStablecoinProvider",
    "mock_stablecoin_provider",
    "get_stablecoin_provider",
]


def get_stablecoin_provider() -> StablecoinProviderInterface:
    """Provider accessor for dependency injection.

    Returns the in-memory mock today. When the Zero Hash integration lands this
    will select a concrete provider from settings (sandbox vs production).
    """
    return mock_stablecoin_provider
