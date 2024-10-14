import re
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Download required NLTK data
nltk.download("punkt_tab", quiet=True)
nltk.download("punkt", quiet=True)
nltk.download("stopwords", quiet=True)


def calculate_text_relevance(
    text: str, keywords: List[str], additional_phrases: List[str]
) -> float:
    """
    Calculate the relevance score for a given text based on keywords and additional phrases.

    :param text: Text to analyze
    :param keywords: List of keywords (mandatory phrases) to search for
    :param additional_phrases: List of additional phrases to search for
    :return: Relevance score
    """
    text = text.lower()

    # Count keyword (mandatory phrase) occurrences with higher weight
    keyword_count = sum(text.count(keyword.lower()) for keyword in keywords)
    keyword_score = keyword_count * 10.0  # Increase weight for mandatory phrases

    # Count additional phrase occurrences
    phrase_count = sum(text.count(phrase.lower()) for phrase in additional_phrases)

    # Tokenize and remove stopwords
    stop_words = set(stopwords.words("english"))
    tokens = [word.lower() for word in word_tokenize(text) if word.isalnum()]
    tokens = [word for word in tokens if word not in stop_words]

    # Calculate unique word ratio
    unique_words = len(set(tokens))
    total_words = len(tokens)
    unique_ratio = unique_words / total_words if total_words > 0 else 0

    # Calculate score
    base_score = keyword_score + phrase_count
    adjusted_score = base_score * (1 + unique_ratio)

    return adjusted_score


def calculate_content_relevance(
    article: Dict[str, Any], keywords: List[str], additional_phrases: List[str]
) -> float:
    """
    Calculate the content relevance score for an article based on keywords and additional phrases.

    :param article: Dictionary containing article information
    :param keywords: List of keywords to search for
    :param additional_phrases: List of additional phrases to search for
    :return: Content relevance score
    """
    title_relevance = calculate_text_relevance(
        article["title"], keywords, additional_phrases
    )
    snippet_relevance = calculate_text_relevance(
        article["snippet"], keywords, additional_phrases
    )

    # Calculate article relevance if full content is available
    article_relevance = 0.0
    if "full_content" in article and article["full_content"]:
        article_relevance = calculate_text_relevance(
            article["full_content"], keywords, additional_phrases
        )

    # Combine relevance scores with weights
    if article_relevance > 0:
        total_relevance = (
            title_relevance * 3 + snippet_relevance * 2 + article_relevance
        ) / 6
    else:
        total_relevance = (title_relevance * 2 + snippet_relevance) / 3

    return total_relevance


def calculate_date_relevance(articles: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate the date relevance for articles based on the number of articles per day.

    :param articles: List of article dictionaries
    :return: Dictionary with dates as keys and relevance scores as values
    """
    date_counter = Counter()

    for article in articles:
        date = datetime.fromtimestamp(article["timestamp"]).date()
        date_counter[date] += 1

    date_relevance = {}
    for date, count in date_counter.items():
        date_relevance[str(date)] = min(count, 5.0)  # Cap the date relevance at 5.0

    return date_relevance


def analyze_articles(
    articles: List[Dict[str, Any]], keywords: List[str], additional_phrases: List[str]
) -> List[Dict[str, Any]]:
    """
    Analyze articles and add a single relevance score.

    :param articles: List of article dictionaries
    :param keywords: List of keywords to search for
    :param additional_phrases: List of additional phrases to search for
    :return: List of articles with added relevance score
    """
    analyzed_articles = []
    date_relevance = calculate_date_relevance(articles)

    for article in articles:
        content_relevance = calculate_content_relevance(
            article, keywords, additional_phrases
        )
        date = str(datetime.fromtimestamp(article["timestamp"]).date())
        date_relevance_score = date_relevance.get(date, 0.0)

        # Combine content and date relevance
        total_relevance = content_relevance + date_relevance_score

        # Normalize the total relevance to be between 0 and 10
        normalized_relevance = min(total_relevance, 10.0)

        # Add the single relevance score to the article
        article["relevance"] = round(normalized_relevance, 2)

        analyzed_articles.append(article)

    return analyzed_articles
