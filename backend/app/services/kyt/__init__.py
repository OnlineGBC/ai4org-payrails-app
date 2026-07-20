"""KYT / blockchain-analytics (sanctions) provider layer.

Mirrors the stablecoin provider structure. MockKytProvider backs dev/tests; a
real provider (Chainalysis / TRM / Elliptic) implements the same interface.
"""
from app.services.kyt.interface import KytProviderInterface
from app.services.kyt.mock_kyt import MockKytProvider, mock_kyt_provider

__all__ = [
    "KytProviderInterface",
    "MockKytProvider",
    "mock_kyt_provider",
    "get_kyt_provider",
]


def get_kyt_provider() -> KytProviderInterface:
    """KYT provider accessor for dependency injection (mock today)."""
    return mock_kyt_provider
