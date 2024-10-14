from datetime import datetime, timezone
from typing import Dict, List

import feedparser

from market_feed.utils.logger import get_logger
from market_feed.utils.relevance_analyzer import analyze_articles

logger = get_logger()


def fetch_rss_feed(feed_url: str) -> List[Dict]:
    """Fetch articles from an RSS feed."""
    logger.info(f"Fetching RSS feed: {feed_url}")
    feed = feedparser.parse(feed_url)
    articles = []

    for entry in feed.entries:
        published = entry.get("published_parsed") or entry.get("updated_parsed")
        if published:
            timestamp = datetime(*published[:6], tzinfo=timezone.utc).timestamp()
            utc_time = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        else:
            timestamp = datetime.now(timezone.utc).timestamp()
            utc_time = datetime.now(timezone.utc)

        articles.append(
            {
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "snippet": entry.get("summary", ""),
                "source": feed.feed.get("title", "Unknown"),
                "timestamp": int(timestamp),
                "utc_time": utc_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            }
        )

    return articles


def fetch_and_analyze_rss_feeds(token: Dict, config: Dict) -> List[Dict]:
    """Fetch and analyze articles from RSS feeds for a given token."""
    default_rss_feeds = config.get("default_rss_feeds", [])
    token_rss_feeds = token.get("rss_feeds", [])
    all_rss_feeds = list(set(default_rss_feeds + token_rss_feeds))

    if not all_rss_feeds:
        logger.info(f"No RSS feeds configured for {token['name']}")
        return []

    all_articles = []
    for feed_url in all_rss_feeds:
        articles = fetch_rss_feed(feed_url)
        all_articles.extend(articles)

    # Analyze article relevance
    keywords = [token["name"], token["symbol"]] + token.get("mandatory_phrases", [])
    additional_phrases = token.get("additional_phrases", [])
    analyzed_articles = analyze_articles(all_articles, keywords, additional_phrases)

    # Filter articles based on relevance threshold
    relevance_threshold = token.get(
        "relevance_threshold", config.get("default_relevance_threshold", 0.5)
    )
    filtered_articles = [
        article
        for article in analyzed_articles
        if article["relevance"] >= relevance_threshold
    ]

    return filtered_articles
