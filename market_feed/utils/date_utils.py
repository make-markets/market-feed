import json
import random
import re
import time
from datetime import datetime, timedelta, timezone
from itertools import cycle
from typing import Callable, Dict, Optional
from urllib import robotparser
from urllib.parse import urlencode, urlparse

import requests
from bs4 import BeautifulSoup
from dateutil import parser

from market_feed.utils.arabic_utils import translate_arabic_date
from market_feed.utils.logger import get_logger

logger = get_logger()


def parse_relative_date(date_string: str) -> int:
    now = datetime.now(timezone.utc)

    # Translate Arabic date to English
    date_string = translate_arabic_date(date_string)

    # Handle special case for Arabic dual form and plurals
    date_string = re.sub(
        r"(\d+)\s*(second|minute|hour|day|week|month|year)", r"\1 \2s", date_string
    )

    if "ago" in date_string.lower():
        # Handle relative dates
        match = re.search(
            r"(\d+)\s*(second|minute|hour|day|week|month|year)s?", date_string.lower()
        )
        if match:
            try:
                value = int(match.group(1))
                unit = match.group(2)
                if unit == "second":
                    delta = timedelta(seconds=value)
                elif unit == "minute":
                    delta = timedelta(minutes=value)
                elif unit == "hour":
                    delta = timedelta(hours=value)
                elif unit == "day":
                    delta = timedelta(days=value)
                elif unit == "week":
                    delta = timedelta(weeks=value)
                elif unit == "month":
                    delta = timedelta(days=value * 30)  # Approximation
                elif unit == "year":
                    delta = timedelta(days=value * 365)  # Approximation
                else:
                    raise ValueError(f"Unrecognized time unit: {unit}")
                return int((now - delta).timestamp())
            except (ValueError, IndexError):
                logger.warning(f"Failed to parse relative date: {date_string}")
    else:
        # Try to parse absolute date
        try:
            date = parser.parse(date_string, fuzzy=True)
            return int(date.replace(tzinfo=timezone.utc).timestamp())
        except ValueError:
            logger.warning(f"Unrecognized date format: {date_string}")

    # If all parsing attempts fail, return current timestamp
    return int(now.timestamp())


def get_random_user_agent() -> str:
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
        # Add more user agents as needed
    ]
    return random.choice(user_agents)


def get_optimized_headers() -> Dict[str, str]:
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }
    return headers


PROXY_LIST = [
    "http://Username:Password@IP1:20000",
    "http://Username:Password@IP2:20000",
    "http://Username:Password@IP3:20000",
    "http://Username:Password@IP4:20000",
    # Add more proxies as needed
]
proxy_pool = cycle(PROXY_LIST)


def get_next_proxy() -> Dict[str, str]:
    proxy = next(proxy_pool)
    return {"http": proxy, "https": proxy}


def can_fetch(url: str, user_agent: str = "*") -> bool:
    parsed_url = urlparse(url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    rp = robotparser.RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception as e:
        logger.warning(f"Failed to parse robots.txt: {e}")
        # If robots.txt cannot be fetched, default to disallow
        return False


def rate_limit(delay: float):
    time.sleep(delay)


def retry_request(
    func: Callable, retries: int = 3, backoff_factor: float = 0.3, *args, **kwargs
) -> requests.Response:
    for attempt in range(retries):
        try:
            response = func(*args, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            if attempt < retries - 1:
                sleep_time = backoff_factor * (2**attempt)
                logger.warning(
                    f"Request failed: {e}. Retrying in {sleep_time} seconds..."
                )
                time.sleep(sleep_time)
            else:
                logger.error(f"All retries failed for request: {e}")
                raise e


def fetch_publication_date(url: str, delay: float = 1.0) -> Optional[int]:
    """
    Fetches the publication date of the given URL while handling potential 403 errors.

    Args:
        url (str): The URL of the web page.
        delay (float): Delay in seconds between requests to respect rate limiting.

    Returns:
        Optional[int]: The publication date as a UTC timestamp if found, otherwise None.
    """
    if not can_fetch(url):
        logger.error(f"Scraping disallowed by robots.txt: {url}")
        return None

    headers = get_optimized_headers()
    proxies = get_next_proxy()

    def make_request():
        return requests.get(url, headers=headers, proxies=proxies, timeout=10)

    try:
        response = retry_request(make_request, retries=5, backoff_factor=0.5)
    except requests.RequestException:
        logger.error(f"Failed to fetch URL after retries: {url}")
        return None

    rate_limit(delay)

    try:
        soup = BeautifulSoup(response.text, "html.parser")

        # List of possible meta tag properties containing the publication date
        meta_properties = [
            ("property", "article:published_time"),
            ("name", "pubdate"),
            ("name", "publication_date"),
            ("name", "date"),
            ("itemprop", "datePublished"),
        ]

        for attr, value in meta_properties:
            tag = soup.find("meta", attrs={attr: value})
            if tag and tag.get("content"):
                try:
                    pub_date = parser.parse(tag["content"])
                    return int(pub_date.replace(tzinfo=timezone.utc).timestamp())
                except (ValueError, TypeError) as e:
                    logger.warning(
                        f"Failed to parse date from meta tag {attr}={value}: {e}"
                    )

        # Attempt to extract date from JSON-LD scripts
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                data = script.string
                if data:
                    json_data = json.loads(data)
                    if isinstance(json_data, dict):
                        date_str = json_data.get("datePublished") or json_data.get(
                            "uploadDate"
                        )
                        if date_str:
                            pub_date = parser.parse(date_str)
                            return int(
                                pub_date.replace(tzinfo=timezone.utc).timestamp()
                            )
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                logger.warning(f"Failed to parse JSON-LD for publication date: {e}")

        # Combined absolute and relative date regex patterns
        date_patterns = [
            r"\d{4}-\d{2}-\d{2}",  # YYYY-MM-DD
            r"\d{2}/\d{2}/\d{4}",  # MM/DD/YYYY or DD/MM/YYYY
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}",  # Month DD, YYYY
            r"\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}",  # DD Month YYYY
            r"\b\d+\s+(?:second|minute|hour|day|week|month|year)s?\s+ago\b",  # Relative timestamps
        ]

        text = soup.get_text()
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    date_str = match.group()
                    if "ago" in date_str.lower():
                        # Use parse_relative_date for relative timestamps
                        return parse_relative_date(date_str)
                    else:
                        # Use dateutil.parser for absolute dates
                        pub_date = parser.parse(date_str, fuzzy=True)
                        return int(pub_date.replace(tzinfo=timezone.utc).timestamp())
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse date from regex match: {e}")

        logger.info(f"No publication date found for URL: {url}")
        return None

    except Exception as e:
        logger.error(f"An error occurred while processing URL {url}: {e}")
        return None
