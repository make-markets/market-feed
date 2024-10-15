import html
import re
from typing import Dict


def truncate_snippet(snippet: str, max_length: int = 500) -> str:
    """Truncate the snippet to a maximum length while preserving readability."""
    decoded_snippet = html.unescape(snippet)
    text_only = re.sub(r"<[^>]+>", "", decoded_snippet)

    if len(text_only) <= max_length:
        return text_only

    truncated = text_only[:max_length]
    last_sentence = truncated.rfind(".")
    return (
        f"{truncated[:last_sentence + 1]} ..."
        if last_sentence > 0
        else f"{truncated}..."
    )


def clean_article(article: Dict) -> Dict:
    """Clean and standardize article data."""
    cleaned_article = article.copy()
    cleaned_article["snippet"] = truncate_snippet(cleaned_article.get("snippet", ""))
    return cleaned_article
