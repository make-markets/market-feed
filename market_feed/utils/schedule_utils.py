import time
from typing import Callable, Dict

import schedule

from market_feed.utils.logger import get_logger

logger = get_logger()


def schedule_token_fetch(
    token: Dict,
    output_dir: str,
    default_interval: int,
    job_creator: Callable,
    config: Dict,
):
    interval = token.get("fetch_interval", default_interval)

    job = job_creator(token, config)

    # Run the job immediately
    job()
    logger.info(f"Ran initial fetch for {token['name']}")

    # Schedule the job to run at regular intervals
    schedule.every(interval).seconds.do(job)
    logger.info(f"Scheduled {token['name']} to fetch every {interval} seconds")


def setup_schedules(
    tokens: list[Dict],
    output_dir: str,
    default_interval: int,
    job_creator: Callable,
    config: Dict,
):
    logger.info("Setting up schedules for all tokens")
    for token in tokens:
        schedule_token_fetch(token, output_dir, default_interval, job_creator, config)
