import os
from typing import Dict, List

import dotenv
from serpapi import GoogleSearch

dotenv.load_dotenv()

params = {
    "api_key": os.getenv("SERP_API_KEY"),  # https://serpapi.com/manage-api-key
    "engine": "google",  # serpapi parsing engine
    "q": "",  # search query
    "tbm": "nws",  # news results
}


def fetch_news(search_phrase: str) -> List[Dict]:
    params["q"] = search_phrase
    search = GoogleSearch(params)  # where data extraction happens on the backend
    results = search.get_dict()  # JSON - > Python dictionary
    return results
