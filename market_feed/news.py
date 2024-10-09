import os
import time
from typing import Dict, List

from dotenv import load_dotenv
from serpapi import GoogleSearch

from market_feed.utils.date_utils import parse_date_to_utc_timestamp

load_dotenv()


def fetch_news(
    token_address: Dict[str, str],
    token_name: str,
    token_symbol: str,
    additional_phrases: List[str] = [],
    max_pages: int = 100,
) -> List[Dict]:
    all_articles = []
    seen_urls = set()
    search_phrase = f"{token_name} {token_symbol}"
    if additional_phrases:
        search_phrase += " " + " ".join(additional_phrases)

    for page in range(max_pages):
        params = {
            "api_key": os.getenv("SERP_API_KEY"),
            "engine": "google",
            "q": search_phrase,
            "tbm": "nws",
            "num": 100,  # Max results per page
            "start": page * 100,
        }

        search = GoogleSearch(params)
        results = search.get_dict()

        if "news_results" not in results:
            break

        for article in results["news_results"]:
            url = article.get("link")
            if url not in seen_urls:
                seen_urls.add(url)
                all_articles.append(
                    {
                        "title": article.get("title"),
                        "name": token_name,
                        "symbol": token_symbol,
                        "address": token_address,
                        "timestamp": parse_date_to_utc_timestamp(article.get("date")),
                        "thumbnail_url": article.get("thumbnail"),
                        "source_url": url,
                        "source_name": article.get("source"),
                        "snippet": article.get("snippet"),
                    }
                )

        if (
            "serpapi_pagination" not in results
            or "next" not in results["serpapi_pagination"]
        ):
            break

        time.sleep(1)  # Respect rate limits

    return all_articles
