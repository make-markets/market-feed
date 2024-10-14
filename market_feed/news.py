import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from itertools import combinations
from typing import Any, Dict, List

from dotenv import load_dotenv
from serpapi import GoogleSearch

from market_feed.rss_feed import fetch_and_analyze_rss_feeds
from market_feed.utils.date_utils import parse_relative_date
from market_feed.utils.json_utils import load_from_json, save_to_json
from market_feed.utils.logger import get_logger
from market_feed.utils.relevance_analyzer import analyze_articles

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
            if results["error"] == "Google hasn't returned any results for this query.":
                logger.info("No results found for this query. Returning empty list.")
                return []
            else:
                raise Exception(f"API Error: {results['error']}")

        # Extract and format the news articles
        news_articles = []
        for result in results.get("news_results", []):
            timestamp = parse_relative_date(result.get("date", ""))
            utc_time = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            news_articles.append(
                {
                    "title": result.get("title"),
                    "link": result.get("link"),
                    "snippet": result.get("snippet"),
                    "source": result.get("source"),
                    "timestamp": timestamp,
                    "utc_time": utc_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
                }
            )

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


def remove_redundant_articles(
    existing_articles: List[Dict], new_articles: List[Dict]
) -> List[Dict]:
    unique_articles = []
    seen_articles = set()

    for article in existing_articles + new_articles:
        article_key = (article["source"], article["link"], article["title"])
        if article_key not in seen_articles:
            unique_articles.append(article)
            seen_articles.add(article_key)

    unique_articles.sort(key=lambda x: x["timestamp"], reverse=True)
    return unique_articles


def get_output_file(token: Dict, output_dir: str) -> str:
    """Generate the output file path for a given token."""
    filename = f"{token['symbol'].lower()}_news.json"
    return os.path.join(output_dir, filename)


def generate_queries(token: Dict) -> List[str]:
    """Generate a list of search queries for a given token."""
    base_query = f"{token['name']} {token['symbol']}"

    # Add mandatory phrases to the base query
    mandatory_phrases = token.get("mandatory_phrases", [])
    if mandatory_phrases:
        base_query += f" {' '.join(mandatory_phrases)}"

    queries = [base_query]

    additional_phrases = token.get("additional_phrases", [])
    if additional_phrases:
        # Generate combinations of additional phrases
        for r in range(1, len(additional_phrases) + 1):
            for combo in combinations(additional_phrases, r):
                query = f"{base_query} {' '.join(combo)}"
                queries.append(query)

    return queries


def fetch_and_update_news(token: Dict, config: Dict):
    logger.info(f"Fetching and updating news for {token['name']} ({token['symbol']})")
    output_dir = config.get("output_dir", "token_news")
    output_file = get_output_file(token, output_dir)
    existing_news = load_from_json(output_file) or []

    # Get the relevance threshold from token config or use the default
    relevance_threshold = token.get(
        "relevance_threshold", config.get("default_relevance_threshold", 0.5)
    )

    if existing_news:
        most_recent_timestamp = max(
            int(article.get("timestamp") or 0) for article in existing_news
        )
        start_date = datetime.fromtimestamp(most_recent_timestamp, tz=timezone.utc)
    else:
        lookback_years = token.get("lookback_years", 2)
        start_date = datetime.now(timezone.utc) - timedelta(days=365 * lookback_years)

    end_date = datetime.now(timezone.utc)

    queries = generate_queries(token)
    all_new_articles = []

    for query in queries:
        logger.info(f"Fetching news for query: {query}")
        new_articles = fetch_news(query, start_date, end_date)
        all_new_articles.extend(new_articles)

    # Fetch RSS feed articles
    rss_articles = fetch_and_analyze_rss_feeds(token, config)
    all_new_articles.extend(rss_articles)

    updated_articles = remove_redundant_articles(existing_news, all_new_articles)

    # Analyze article relevance
    keywords = [token["name"], token["symbol"]] + token.get("mandatory_phrases", [])
    additional_phrases = token.get("additional_phrases", [])
    analyzed_articles = analyze_articles(updated_articles, keywords, additional_phrases)

    # Filter articles based on relevance threshold
    filtered_articles = [
        article
        for article in analyzed_articles
        if article["relevance"] >= relevance_threshold
    ]

    save_to_json(filtered_articles, output_file)

    new_articles_count = len(filtered_articles) - len(existing_news)
    logger.info(
        f"Added {new_articles_count} new relevant articles for {token['name']}. Total articles: {len(filtered_articles)}"
    )

    # Log headlines and relevance scores of new articles
    for article in filtered_articles[:new_articles_count]:
        logger.info(
            f"New article for {token['name']}: {article['title']} (Relevance: {article['relevance']})"
        )
