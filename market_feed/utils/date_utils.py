import json
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests
from bs4 import BeautifulSoup
from dateutil import parser

from market_feed.utils.logger import get_logger

logger = get_logger()


def parse_relative_date(date_string: str) -> int:
    now = datetime.now(timezone.utc)

    if "ago" in date_string.lower():
        # Handle relative dates
        parts = date_string.lower().split()
        if len(parts) >= 2:
            try:
                value = int(parts[0])
                unit = parts[1]
                if unit.startswith("second"):
                    delta = timedelta(seconds=value)
                elif unit.startswith("minute"):
                    delta = timedelta(minutes=value)
                elif unit.startswith("hour"):
                    delta = timedelta(hours=value)
                elif unit.startswith("day"):
                    delta = timedelta(days=value)
                elif unit.startswith("week"):
                    delta = timedelta(weeks=value)
                elif unit.startswith("month"):
                    delta = timedelta(days=value * 30)  # Approximation
                elif unit.startswith("year"):
                    delta = timedelta(days=value * 365)  # Approximation
                else:
                    raise ValueError(f"Unrecognized time unit: {unit}")
                return int((now - delta).timestamp())
            except (ValueError, IndexError):
                logger.warning(f"Failed to parse relative date: {date_string}")
    else:
        # Try to parse absolute date
        try:
            date = datetime.strptime(date_string, "%b %d, %Y")
            date = date.replace(
                hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
            )
            return int(date.timestamp())
        except ValueError:
            logger.warning(f"Unrecognized date format: {date_string}")

    # If all parsing attempts fail, return current timestamp
    return int(now.timestamp())


def fetch_publication_date(url: str) -> Optional[int]:
    """
    Fetches the publication date of the given URL.

    Args:
        url (str): The URL of the web page.

    Returns:
        Optional[int]: The publication date as a UTC timestamp if found, otherwise None.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
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

        logger.info(f"No publication date found for URL: {url}")
        return None

    except requests.RequestException as e:
        logger.error(f"Request failed for URL {url}: {e}")
        return None
