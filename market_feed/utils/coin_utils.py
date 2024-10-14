from typing import List, Optional, Tuple

from web3 import Web3
from web3.exceptions import ContractLogicError

from .chainlist_utils import get_rpc_urls

# ABI for ERC20 token interface (minimal for name and symbol)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
]


def get_web3_instance(rpc_url: str) -> Optional[Web3]:
    """
    Create a Web3 instance for the given RPC URL.

    Args:
        rpc_url (str): The RPC URL

    Returns:
        Optional[Web3]: A connected Web3 instance or None if connection fails
    """
    try:
        web3 = Web3(Web3.HTTPProvider(rpc_url))
        if web3.is_connected():
            return web3
    except Exception:
        pass
    return None


def get_working_web3_instance(chain_id: int) -> Web3:
    """
    Try to get a working Web3 instance for the given chain ID.

    Args:
        chain_id (int): The chain ID

    Returns:
        Web3: A connected Web3 instance

    Raises:
        ValueError: If no working RPC is found for the chain ID
    """
    rpc_urls = get_rpc_urls(chain_id)
    if not rpc_urls:
        raise ValueError(f"No RPC URLs found for chain ID: {chain_id}")

    for rpc_url in rpc_urls:
        web3 = get_web3_instance(rpc_url)
        if web3:
            return web3

    raise ValueError(f"Failed to connect to any RPC for chain ID: {chain_id}")


def fetch_token_info(address: str, chain_id: int) -> Optional[Tuple[str, str]]:
    """
    Fetch the name and symbol of a token given its address and chain ID.

    Args:
        address (str): The token contract address
        chain_id (int): The chain ID

    Returns:
        Optional[Tuple[str, str]]: A tuple containing (name, symbol) if successful, None otherwise
    """
    rpc_urls = get_rpc_urls(chain_id)
    if not rpc_urls:
        print(f"No RPC URLs found for chain ID: {chain_id}")
        return None

    for rpc_url in rpc_urls:
        try:
            web3 = get_web3_instance(rpc_url)
            if not web3:
                continue

            if not web3.is_address(address):
                print(f"Invalid address: {address}")
                return None

            contract = web3.eth.contract(
                address=Web3.to_checksum_address(address), abi=ERC20_ABI
            )

            name = contract.functions.name().call()
            symbol = contract.functions.symbol().call()

            return name, symbol
        except ContractLogicError as e:
            print(f"Contract error for address {address} on RPC {rpc_url}: {str(e)}")
        except Exception as e:
            print(
                f"Error fetching token info for address {address} on RPC {rpc_url}: {str(e)}"
            )

    print(
        f"Failed to fetch token info for address {address} on all RPCs for chain ID {chain_id}"
    )
    return None


# Example usage
if __name__ == "__main__":
    # Example token address (USDT on Ethereum)
    token_address = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
    ethereum_chain_id = 1

    result = fetch_token_info(token_address, ethereum_chain_id)
    if result:
        name, symbol = result
        print(f"Token Name: {name}")
        print(f"Token Symbol: {symbol}")
    else:
        print("Failed to fetch token information")

    # Example for BSC using chain ID
    bsc_token_address = "0x55d398326f99059fF775485246999027B3197955"  # BSC USDT
    bsc_chain_id = 56

    bsc_result = fetch_token_info(bsc_token_address, bsc_chain_id)
    if bsc_result:
        bsc_name, bsc_symbol = bsc_result
        print(f"BSC Token Name: {bsc_name}")
        print(f"BSC Token Symbol: {bsc_symbol}")
    else:
        print("Failed to fetch BSC token information")
