from typing import Optional, Tuple, Union

from chainlist_utils import get_chain_id, get_rpc_urls
from web3 import Web3
from web3.exceptions import ContractLogicError

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


def get_web3_instance(network: Union[str, int]) -> Web3:
    """
    Create a Web3 instance for the given network using chainlist_utils.

    Args:
        network (Union[str, int]): The network name or chain ID

    Returns:
        Web3: A connected Web3 instance

    Raises:
        ValueError: If no RPC URLs are found or connection fails
    """
    if isinstance(network, str):
        chain_id = get_chain_id(network)
        if chain_id is None:
            raise ValueError(f"No chain ID found for network name: {network}")
    else:
        chain_id = int(network)

    rpc_urls = get_rpc_urls(chain_id)
    if not rpc_urls:
        raise ValueError(f"No RPC URLs found for chain ID: {chain_id}")

    # Try RPC URLs until a working one is found
    for rpc_url in rpc_urls:
        try:
            web3 = Web3(Web3.HTTPProvider(rpc_url))
            if web3.is_connected():
                return web3
        except Exception:
            continue

    raise ValueError(f"Failed to connect to any RPC for chain ID: {chain_id}")


def fetch_token_info(
    address: str, network: Union[str, int]
) -> Optional[Tuple[str, str]]:
    """
    Fetch the name and symbol of a token given its address and network.

    Args:
        address (str): The token contract address
        network (Union[str, int]): The network name or chain ID

    Returns:
        Optional[Tuple[str, str]]: A tuple containing (name, symbol) if successful, None otherwise
    """
    try:
        web3 = get_web3_instance(network)

        # Ensure the address is valid
        if not web3.is_address(address):
            print(f"Invalid address: {address}")
            return None

        # Create contract instance
        contract = web3.eth.contract(
            address=Web3.to_checksum_address(address), abi=ERC20_ABI
        )

        # Fetch name and symbol
        name = contract.functions.name().call()
        symbol = contract.functions.symbol().call()

        return name, symbol
    except ContractLogicError as e:
        print(f"Contract error for address {address}: {str(e)}")
    except Exception as e:
        print(f"Error fetching token info for address {address}: {str(e)}")

    return None


# Example usage
if __name__ == "__main__":
    # Example token address (USDT on Ethereum)
    token_address = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
    network = 1  # Ethereum chain ID

    result = fetch_token_info(token_address, network)
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
