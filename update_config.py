import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from typing import Any, Dict, List

import requests
import yaml

from market_feed.utils.coin_utils import fetch_token_info
from market_feed.utils.logger import get_logger
from market_feed.utils.schedule_utils import setup_schedules

CURVE_TOKEN_API = "https://api.curve.fi/api/getTokens/all/"
CURVE_PLATFORM_API = "https://api.curve.fi/api/getPlatforms/"
CONFIG_FILE = "config.yaml"
DEFAULT_FETCH_INTERVAL = 3600  # 1 hour in seconds
LOOKBACK_YEARS = 2
NATIVE_TOKEN_ADDRESS = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"

logger = get_logger()


def get_networks() -> Dict[str, int]:
    logger.info("Fetching network information from Curve API")
    response = requests.get(CURVE_PLATFORM_API)
    response.raise_for_status()
    networks = response.json()["data"]["platformToChainIdMap"]
    logger.info(f"Successfully fetched information for {len(networks)} networks")
    return networks


def load_existing_config() -> Dict[str, Any]:
    default_config = {
        "tokens": [],
        "output_directory": "token_news",
        "default_fetch_interval": DEFAULT_FETCH_INTERVAL,
        "default_relevance_threshold": 0.5,  # Add default relevance threshold
    }

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = yaml.safe_load(f)

            if not isinstance(config, dict):
                logger.warning(
                    "Existing config file is not properly formatted. Using default configuration."
                )
                return default_config

            # Ensure all required keys are present
            for key in default_config.keys():
                if key not in config:
                    logger.warning(
                        f"Missing '{key}' in config file. Adding default value."
                    )
                    config[key] = default_config[key]

            # Ensure 'tokens' is a list
            if not isinstance(config["tokens"], list):
                logger.warning(
                    "'tokens' in config file is not a list. Resetting to empty list."
                )
                config["tokens"] = []

            return config
        except yaml.YAMLError as e:
            logger.error(
                f"Error parsing existing config file: {str(e)}. Using default configuration."
            )
            return default_config
    else:
        logger.info("Config file not found. Creating new configuration.")
        return default_config


def save_config(config: Dict[str, Any]):
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    logger.info("Config file updated successfully")


def create_token_config(coin_info: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": coin_info["name"],
        "symbol": coin_info["symbol"],
        "address": {coin_info["network"]: coin_info["address"]},
        "mandatory_phrases": [],
        "additional_phrases": ["defi"],
        "lookback_years": LOOKBACK_YEARS,
        "relevance_threshold": None,  # Add relevance_threshold field, set to None by default
    }


def token_exists(token: Dict[str, Any], existing_tokens: List[Dict[str, Any]]) -> bool:
    for existing_token in existing_tokens:
        if (
            token["symbol"] == existing_token["symbol"]
            and token["address"] == existing_token["address"]
        ):
            return True
    return False


def fetch_and_update_coins(networks: Dict[str, int], config: Dict[str, Any]) -> int:
    new_tokens_count = 0
    total_networks = len(networks)
    for index, (network, chain_id) in enumerate(networks.items(), 1):
        logger.info(
            f"Fetching tokens for network: {network} (Chain ID: {chain_id}) - {index}/{total_networks}"
        )
        response = requests.get(CURVE_TOKEN_API + network)
        response.raise_for_status()
        tokens = response.json()["data"]["tokens"]
        logger.info(f"Found {len(tokens)} tokens on {network}")

        for token in tokens:
            if token["address"].lower() == NATIVE_TOKEN_ADDRESS.lower():
                logger.info(f"Skipping native token on {network}")
                continue

            token["network"] = network
            token["chain_id"] = chain_id
            if not token_exists(token, config["tokens"]):
                logger.debug(
                    f"Fetching additional info for new token: {token['address']} on {network}"
                )
                token_info = fetch_token_info(token["address"], chain_id)
                if token_info:
                    token["name"], token["symbol"] = token_info
                    new_token_config = create_token_config(token)
                    config["tokens"].append(new_token_config)
                    new_tokens_count += 1
                    logger.info(
                        f"Added new token: {token['name']} ({token['symbol']}) on {network}"
                    )
                    save_config(config)
                else:
                    logger.warning(
                        f"Failed to fetch info for token {token['address']} on chain {chain_id}"
                    )

    return new_tokens_count


def update_config():
    start_time = time.time()
    logger.info("Starting config update process")
    try:
        config = load_existing_config()
        networks = get_networks()
        new_tokens_count = fetch_and_update_coins(networks, config)

        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Config update process completed in {duration:.2f} seconds")
        logger.info(
            f"Added {new_tokens_count} new tokens. Total tokens: {len(config['tokens'])}"
        )
    except Exception as e:
        logger.error(f"Error updating config: {str(e)}", exc_info=True)


def run_update_config():
    logger.info("Running config update")
    update_config()
    logger.info("Config update completed")


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
    import schedule

    while True:
        schedule.run_pending()
        time.sleep(1)
