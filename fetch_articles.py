import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from market_feed.config import load_config
from market_feed.utils.logger import get_logger
from market_feed.utils.schedule_utils import initialize_scheduler, run_scheduler

logger = get_logger()


def main():
    logger.info("Starting the news fetching service")
    config = load_config()
    logger.info("Configuration loaded successfully")
    initialize_scheduler(config)
    logger.info("Scheduler initialized, starting to run")
    run_scheduler()


if __name__ == "__main__":
    main()
