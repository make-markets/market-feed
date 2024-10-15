from datetime import datetime, timezone
from typing import Dict, List

import feedparser

from market_feed.utils.content_utils import clean_article
from market_feed.utils.logger import get_logger

logger = get_logger()


def parse_feed_entry(entry: Dict, feed_title: str, tag: str, is_default: bool) -> Dict:
    published = entry.get("published_parsed") or entry.get("updated_parsed")
    timestamp = (
        datetime(*published[:6], tzinfo=timezone.utc).timestamp()
        if published
        else datetime.now(timezone.utc).timestamp()
    )
    utc_time = datetime.fromtimestamp(timestamp, tz=timezone.utc)

    article = clean_article(
        {
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "snippet": entry.get("summary", ""),
            "source": feed_title,
            "timestamp": int(timestamp),
            "utc_time": utc_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "tag": tag,
        }
    )

    if not is_default:
        article["relevance"] = 10.0

    return article


def fetch_rss_feed(feed_url: str, tag: str, is_default: bool) -> List[Dict]:
    """Fetch articles from an RSS feed."""
    logger.info(f"Fetching RSS feed: {feed_url}")
    feed = feedparser.parse(feed_url)
    feed_title = feed.feed.get("title", "Unknown")
    return [
        parse_feed_entry(entry, feed_title, tag, is_default) for entry in feed.entries
    ]


def fetch_token_rss(token: Dict, default_rss_feeds: List[str]) -> List[Dict]:
    """Fetch articles from RSS feeds for a given token."""
    default_articles = [
        article
        for feed_url in default_rss_feeds
        for article in fetch_rss_feed(feed_url, tag="independent-news", is_default=True)
    ]

    token_articles = [
        article
        for feed in token.get("rss_feeds", [])
        for article in fetch_rss_feed(feed["url"], tag=feed["tag"], is_default=False)
    ]

    return default_articles + token_articles
