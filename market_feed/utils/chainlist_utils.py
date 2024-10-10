import requests

CHAINIDS_URL = (
    "https://raw.githubusercontent.com/DefiLlama/chainlist/main/constants/chainIds.json"
)
RPCS_URL = "https://chainlist.org/rpcs.json"


def load_data():
    """Load chain IDs and RPCs data from URLs."""
    chain_ids = requests.get(CHAINIDS_URL).json()
    rpcs = requests.get(RPCS_URL).json()
    return chain_ids, rpcs


CHAIN_IDS, RPCS = load_data()


def get_chain_id(chain_name):
    """
    Get the chain ID for a given chain name.

    :param chain_name: Name of the chain
    :return: Chain ID if found, None otherwise
    """
    for chain_id, name in CHAIN_IDS.items():
        if name.lower() == chain_name.lower():
            return int(chain_id)
    return None


def get_chain_name(chain_id):
    """
    Get the chain name for a given chain ID.

    :param chain_id: ID of the chain
    :return: Chain name if found, None otherwise
    """
    return CHAIN_IDS.get(str(chain_id))


def get_rpc_urls(chain_id: int):
    """
    Get RPC URLs for a given chain ID.

    :param chain_id: Chain ID (int)
    :return: List of RPC URLs if found, empty list otherwise
    """
    for chain in RPCS:
        if chain.get("chainId") == chain_id:
            return [rpc["url"] for rpc in chain.get("rpc", [])]
    return []


def refresh_data():
    """Refresh the chain IDs and RPCs data."""
    global CHAIN_IDS, RPCS
    CHAIN_IDS, RPCS = load_data()


def main():
    print("Testing chainlist_utils.py functionality:")

    # Test get_chain_id
    eth_id = get_chain_id("ethereum")
    print(f"Ethereum chain ID: {eth_id}")

    bsc_id = get_chain_id("Binance Smart Chain")
    print(f"Binance Smart Chain ID: {bsc_id}")

    # Test get_chain_name
    eth_name = get_chain_name(1)
    print(f"Chain name for ID 1: {eth_name}")

    bsc_name = get_chain_name(56)
    print(f"Chain name for ID 56: {bsc_name}")

    # Test get_rpc_urls
    eth_rpcs = get_rpc_urls(1)  # Ethereum
    print(f"Ethereum RPC URLs (first 3): {eth_rpcs[:3]}")

    bsc_rpcs = get_rpc_urls(56)  # BSC
    print(f"BSC RPC URLs (first 3): {bsc_rpcs[:3]}")

    # Test with an invalid chain ID
    invalid_rpcs = get_rpc_urls(999999)
    print(f"Invalid chain RPC URLs: {invalid_rpcs}")


if __name__ == "__main__":
    main()
