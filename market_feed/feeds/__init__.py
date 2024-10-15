from datetime import datetime, timedelta, timezone
from typing import Dict, List

from market_feed.feeds.news import fetch_token_news
from market_feed.feeds.rss import fetch_token_rss
from market_feed.utils.json_utils import load_from_json, save_to_json
from market_feed.utils.logger import get_logger
from market_feed.utils.relevance_analyzer import analyze_articles

logger = get_logger()


def get_output_file(token: Dict, output_dir: str) -> str:
    return f"{output_dir}/{token['symbol'].lower()}_news.json"


def remove_duplicates(articles: List[Dict]) -> List[Dict]:
    unique_articles = {}
    for article in articles:
        key = (article["source"], article["link"], article["title"])
        if (
            key not in unique_articles
            or article["timestamp"] > unique_articles[key]["timestamp"]
        ):
            unique_articles[key] = article
    return list(unique_articles.values())


def filter_and_sort_articles(
    articles: List[Dict], relevance_threshold: float
) -> List[Dict]:
    filtered_articles = [
        {k: v for k, v in article.items() if k != "relevance"}
        for article in articles
        if article.get("relevance", 0) >= relevance_threshold
    ]
    return sorted(filtered_articles, key=lambda x: x["timestamp"], reverse=True)


def get_content(token: Dict, config: Dict):
    logger.info(f"Fetching and updating news for {token['name']} ({token['symbol']})")
    output_file = get_output_file(token, config.get("output_dir", "token_news"))
    existing_news = load_from_json(output_file) or []

    relevance_threshold = token.get(
        "relevance_threshold", config.get("default_relevance_threshold", 0.5)
    )

    if existing_news:
        start_date = datetime.fromtimestamp(
            max(int(article.get("timestamp") or 0) for article in existing_news),
            tz=timezone.utc,
        )
    else:
        start_date = datetime.now(timezone.utc) - timedelta(
            days=365 * token.get("lookback_years", 2)
        )

    end_date = datetime.now(timezone.utc)

    new_articles = fetch_token_news(token, start_date, end_date)
    rss_articles = fetch_token_rss(token, config.get("default_rss_feeds", []))

    all_articles = remove_duplicates(existing_news + new_articles + rss_articles)

    keywords = [token["name"], token["symbol"]] + token.get("mandatory_phrases", [])
    additional_phrases = token.get("additional_phrases", [])

    analyzed_articles = [
        article
        if "relevance" in article
        else analyze_articles([article], keywords, additional_phrases)[0]
        for article in all_articles
    ]

    filtered_articles = filter_and_sort_articles(analyzed_articles, relevance_threshold)

    save_to_json(filtered_articles, output_file)

    new_articles_count = len(filtered_articles) - len(existing_news)
    logger.info(
        f"Added {new_articles_count} new relevant articles for {token['name']}. Total articles: {len(filtered_articles)}"
    )

    for article in filtered_articles[:new_articles_count]:
        logger.info(f"New article for {token['name']}: {article['title']}")
