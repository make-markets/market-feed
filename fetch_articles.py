import os
import time
from typing import Dict

import schedule

from market_feed.config import load_config
from market_feed.news import fetch_news
from market_feed.utils.json_utils import load_from_json, save_to_json


def get_output_file(token: Dict, output_dir: str) -> str:
    """Generate the output file path for a given token."""
    filename = f"{token['symbol'].lower()}_news.json"
    return os.path.join(output_dir, filename)


def fetch_and_update_news(token: Dict, output_dir: str):
    output_file = get_output_file(token, output_dir)
    all_news = load_from_json(output_file) or []

    news_articles = fetch_news(
        token["address"],
        token["name"],
        token["symbol"],
        token.get("additional_phrases", []),
    )

    # Add only new articles
    new_articles = [article for article in news_articles if article not in all_news]
    all_news.extend(new_articles)

    save_to_json(all_news, output_file)
    print(
        f"Fetched {len(new_articles)} new articles for {token['name']}. Total articles: {len(all_news)}"
    )


def schedule_token_fetch(token: Dict, output_dir: str, default_interval: int):
    interval = token.get("fetch_interval", default_interval)
    schedule.every(interval).seconds.do(fetch_and_update_news, token, output_dir)
    print(f"Scheduled {token['name']} to fetch every {interval} seconds")


def main():
    config = load_config()
    tokens = config["tokens"]
    output_dir = config["output_directory"]
    default_interval = config["default_fetch_interval"]

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    print(
        f"Starting news fetching service. Default interval: {default_interval} seconds"
    )

    for token in tokens:
        schedule_token_fetch(token, output_dir, default_interval)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
