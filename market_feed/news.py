import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from dotenv import load_dotenv
from serpapi import GoogleSearch

from market_feed.utils.date_utils import fetch_publication_date, parse_relative_date
from market_feed.utils.json_utils import load_from_json, save_to_json
from market_feed.utils.logger import get_logger

logger = get_logger()

# Load environment variables from .env file
load_dotenv()


def fetch_news(query: str, start_date: datetime, end_date: datetime) -> List[Dict]:
    logger.info(f"Fetching news for query: {query} from {start_date} to {end_date}")

    # Set up the search parameters
    params = {
        "q": query,
        "tbm": "nws",
        "num": 100,  # Increase the number of results
        "api_key": os.getenv("SERP_API_KEY"),
        "tbs": f"cdr:1,cd_min:{start_date.strftime('%m/%d/%Y')},cd_max:{end_date.strftime('%m/%d/%Y')}",
    }

    all_news_articles = []
    page = 1

    while True:
        logger.info(f"Fetching page {page} for query: {query}")

        # Add pagination parameter
        if page > 1:
            params["start"] = (page - 1) * 100

        # Perform the search
        search = GoogleSearch(params)
        results = search.get_dict()

        if "error" in results:
            logger.error(f"API Error: {results['error']}")
            raise Exception(f"API Error: {results['error']}")

        # Extract and format the news articles
        news_articles = []
        for result in results.get("news_results", []):
            url = result.get("link")
            timestamp_bs4 = fetch_publication_date(url)
            posted_relative_date = parse_relative_date(result.get("date", ""))

            article = {
                "title": result.get("title"),
                "link": result.get("link"),
                "snippet": result.get("snippet"),
                "source": result.get("source"),
                "timestamp_bs4": timestamp_bs4,
                "timestamp_relative": posted_relative_date,
            }
            news_articles.append(article)

        all_news_articles.extend(news_articles)

        # Check if there are more pages
        if (
            "serpapi_pagination" not in results
            or "next" not in results["serpapi_pagination"]
        ):
            break

        page += 1

    logger.info(f"Fetched a total of {len(all_news_articles)} news articles")
    return all_news_articles


def get_output_file(token: Dict, output_dir: str) -> str:
    """Generate the output file path for a given token."""
    filename = f"{token['symbol'].lower()}_news.json"
    return os.path.join(output_dir, filename)


def fetch_and_update_news(token: Dict, output_dir: str):
    logger.info(f"Fetching and updating news for {token['name']} ({token['symbol']})")
    output_file = get_output_file(token, output_dir)
    all_news = load_from_json(output_file) or []

    # Determine the start date for fetching news
    if all_news:
        # Get the most recent article's timestamp
        most_recent_timestamp = max(
            max(
                int(article.get("timestamp_bs4") or 0),
                int(article.get("timestamp_relative") or 0),
            )
            for article in all_news
        )
        start_date = datetime.fromtimestamp(most_recent_timestamp, tz=timezone.utc)
    else:
        # If no existing articles, use the lookback_years from config
        lookback_years = token.get("lookback_years", 2)
        start_date = datetime.now(timezone.utc) - timedelta(days=365 * lookback_years)

    end_date = datetime.now(timezone.utc)

    # Construct the search query
    query = f"{token['name']} {token['symbol']}"
    if additional_phrases := token.get("additional_phrases", []):
        query += " " + " ".join(additional_phrases)

    news_articles = fetch_news(query, start_date, end_date)

    # Add only new articles
    new_articles = [article for article in news_articles if article not in all_news]
    all_news.extend(new_articles)

    save_to_json(all_news, output_file)
    logger.info(
        f"Fetched {len(new_articles)} new articles for {token['name']}. Total articles: {len(all_news)}"
    )
