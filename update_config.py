import asyncio
from functools import reduce
from typing import Any, Dict, List, Set

import httpx
import yaml

from market_feed.utils.logger import get_logger
from market_feed.utils.schedule_utils import setup_schedules

API_URL = "https://api.curve.fi/api/getPools/big"
CONFIG_FILE = "config.yaml"
DEFAULT_FETCH_INTERVAL = 3600  # 1 hour in seconds
LOOKBACK_YEARS = 2

logger = get_logger()


async def fetch_pools() -> List[Dict[str, Any]]:
    async with httpx.AsyncClient() as client:
        response = await client.get(API_URL)
        response.raise_for_status()
        return response.json()["data"]["poolData"]


def extract_coins(pools: List[Dict[str, Any]]) -> Set[str]:
    coin_addresses = set()
    for pool in pools:
        breakpoint()
        network = pool["blockchainId"]
        for coin_address in pool["coinsAddresses"]:
            coin_addresses.add((network, coin_address))
    return coin_addresses


def create_token_config(coin_info: tuple) -> Dict[str, Any]:
    network, address = coin_info
    return {
        "symbol": address,
        "address": {network: address},
        "additional_phrases": ["stablecoin"],
        "lookback_years": LOOKBACK_YEARS,
    }


def create_config(coins: Set[tuple]) -> Dict[str, Any]:
    return {
        "tokens": [create_token_config(coin) for coin in coins],
        "output_directory": "token_news",
        "default_fetch_interval": DEFAULT_FETCH_INTERVAL,
    }


async def update_config():
    try:
        pools = await fetch_pools()
        coins = extract_coins(pools)
        config = create_config(coins)

        with open(CONFIG_FILE, "w") as f:
            yaml.dump(config, f, default_flow_style=False)
        logger.info("Config file updated successfully")
    except Exception as e:
        logger.error(f"Error updating config: {str(e)}")


def run_update_config():
    asyncio.run(update_config())


if __name__ == "__main__":
    # Run the job immediately
    logger.info("Running initial config update")
    run_update_config()

    # Create a dummy token for scheduling
    config_update_token = {
        "name": "Config Update",
        "fetch_interval": DEFAULT_FETCH_INTERVAL,
    }

    # Schedule the job to run at regular intervals
    setup_schedules(
        tokens=[config_update_token],
        output_dir="",  # Not used for this job
        default_interval=DEFAULT_FETCH_INTERVAL,
        job_creator=lambda token, config: run_update_config,
        config={},  # Not used for this job
    )

    logger.info(
        f"Scheduled config update to run every {DEFAULT_FETCH_INTERVAL} seconds"
    )

    # Start the scheduler
    import time

    import schedule

    while True:
        schedule.run_pending()
        time.sleep(1)
