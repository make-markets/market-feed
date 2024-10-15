import os
from datetime import datetime, timezone
from itertools import combinations
from typing import Dict, List

from dotenv import load_dotenv
from serpapi import GoogleSearch

from market_feed.utils.content_utils import clean_article
from market_feed.utils.date_utils import parse_relative_date
from market_feed.utils.logger import get_logger

logger = get_logger()

load_dotenv()


def fetch_news_page(
    query: str, start_date: datetime, end_date: datetime, page: int
) -> List[Dict]:
    params = {
        "q": query,
        "tbm": "nws",
        "num": 100,
        "api_key": os.getenv("SERP_API_KEY"),
        "tbs": f"cdr:1,cd_min:{start_date.strftime('%m/%d/%Y')},cd_max:{end_date.strftime('%m/%d/%Y')}",
        "start": (page - 1) * 100 if page > 1 else None,
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    if "error" in results:
        logger.error(f"API Error: {results['error']}")
        return []

    return [
        clean_article(
            {
                "title": result.get("title"),
                "link": result.get("link"),
                "snippet": result.get("snippet"),
                "source": result.get("source"),
                "timestamp": parse_relative_date(result.get("date", "")),
                "utc_time": datetime.fromtimestamp(
                    parse_relative_date(result.get("date", "")), tz=timezone.utc
                ).strftime("%Y-%m-%d %H:%M:%S UTC"),
                "tag": "independent-news",
            }
        )
        for result in results.get("news_results", [])
    ]


def fetch_news(query: str, start_date: datetime, end_date: datetime) -> List[Dict]:
    logger.info(f"Fetching news for query: {query} from {start_date} to {end_date}")
    all_news_articles = []
    page = 1

    while True:
        logger.info(f"Fetching page {page} for query: {query}")
        news_articles = fetch_news_page(query, start_date, end_date, page)
        all_news_articles.extend(news_articles)

        if len(news_articles) < 100:
            break
        page += 1

    logger.info(f"Fetched a total of {len(all_news_articles)} news articles")
    return all_news_articles


def generate_queries(token: Dict) -> List[str]:
    base_query = f"{token['name']} {token['symbol']} {' '.join(token.get('mandatory_phrases', []))}"
    queries = [base_query]

    additional_phrases = token.get("additional_phrases", [])
    for r in range(1, len(additional_phrases) + 1):
        queries.extend(
            f"{base_query} {' '.join(combo)}"
            for combo in combinations(additional_phrases, r)
        )

    return queries


def fetch_token_news(
    token: Dict, start_date: datetime, end_date: datetime
) -> List[Dict]:
    queries = generate_queries(token)
    return [
        article
        for query in queries
        for article in fetch_news(query, start_date, end_date)
    ]
