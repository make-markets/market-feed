import os
import sys
import time
from typing import Dict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from market_feed.feeds import get_content
from market_feed.utils.config_utils import load_config
from market_feed.utils.logger import get_logger
from market_feed.utils.schedule_utils import setup_schedules

logger = get_logger()


def create_job(token: Dict, config: Dict):
    return lambda: get_content(token, config)


def main():
    logger.info("Starting the news fetching service")

    config = load_config()
    tokens = config.get("tokens", [])
    output_dir = config.get("output_directory", "token_news")
    default_interval = config.get(
        "default_fetch_interval", 3600
    )  # Default to 1 hour if not specified

    if not tokens:
        logger.error("No tokens found in the configuration. Exiting.")
        return

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Setup schedules for all tokens
    setup_schedules(tokens, output_dir, default_interval, create_job, config)

    logger.info("All schedules set up. Running jobs...")

    # Run the scheduler
    while True:
        try:
            import schedule

            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received. Exiting.")
            break
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            logger.info("Retrying in 60 seconds...")
            time.sleep(60)


if __name__ == "__main__":
    main()
