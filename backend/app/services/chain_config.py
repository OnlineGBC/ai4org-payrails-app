"""Per-chain configuration for stablecoin networks.

Confirmation thresholds gate when an on-chain transfer is treated as final.
The `asset_networks` table can override these per (asset, network); this map is
the default and the source of truth for which networks are accepted.
"""

# network -> default minimum confirmations before a transfer is 'confirmed'
NETWORK_MIN_CONFIRMATIONS = {
    "ethereum": 12,
    "solana": 32,
    "bnb": 15,
}

SUPPORTED_NETWORKS = frozenset(NETWORK_MIN_CONFIRMATIONS.keys())


def is_supported_network(network: str) -> bool:
    return network in SUPPORTED_NETWORKS


def min_confirmations_for(network: str) -> int:
    return NETWORK_MIN_CONFIRMATIONS.get(network, 12)
