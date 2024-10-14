from datetime import datetime, timezone
from typing import Dict, List

import feedparser

from market_feed.utils.logger import get_logger

logger = get_logger()


def fetch_rss_feed(feed_url: str, is_token_specific: bool) -> List[Dict]:
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

        article = {
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "snippet": entry.get("summary", ""),
            "source": feed.feed.get("title", "Unknown"),
            "timestamp": int(timestamp),
            "utc_time": utc_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
        }

        if is_token_specific:
            article["relevance"] = 10.0

        articles.append(article)

    return articles


def fetch_rss_feeds(token: Dict, config: Dict) -> List[Dict]:
    """Fetch articles from RSS feeds for a given token."""
    default_rss_feeds = config.get("default_rss_feeds", [])
    token_rss_feeds = token.get("rss_feeds", [])

    all_articles = []

    # Fetch articles from default RSS feeds
    for feed_url in default_rss_feeds:
        articles = fetch_rss_feed(feed_url, is_token_specific=False)
        all_articles.extend(articles)

    # Fetch articles from token-specific RSS feeds
    for feed_url in token_rss_feeds:
        articles = fetch_rss_feed(feed_url, is_token_specific=True)
        all_articles.extend(articles)

    return all_articles
