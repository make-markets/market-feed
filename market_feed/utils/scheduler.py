import os
import time
from typing import Dict

import schedule

from market_feed.news import fetch_and_update_news
from market_feed.utils.logger import get_logger

logger = get_logger()


def schedule_token_fetch(token: Dict, output_dir: str, default_interval: int):
    interval = token.get("fetch_interval", default_interval)

    # Run the job immediately
    fetch_and_update_news(token, output_dir)
    logger.info(f"Ran initial fetch for {token['name']}")

    # Schedule the job to run at regular intervals
    schedule.every(interval).seconds.do(fetch_and_update_news, token, output_dir)
    logger.info(f"Scheduled {token['name']} to fetch every {interval} seconds")


def run_scheduler():
    logger.info("Starting scheduler")
    while True:
        schedule.run_pending()
        time.sleep(1)


def setup_schedules(tokens: list[Dict], output_dir: str, default_interval: int):
    logger.info("Setting up schedules for all tokens")
    for token in tokens:
        schedule_token_fetch(token, output_dir, default_interval)


def initialize_scheduler(config: Dict):
    tokens = config["tokens"]
    output_dir = config["output_directory"]
    default_interval = config["default_fetch_interval"]

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Ensured output directory exists: {output_dir}")

    logger.info(
        f"Starting news fetching service. Default interval: {default_interval} seconds"
    )

    setup_schedules(tokens, output_dir, default_interval)
