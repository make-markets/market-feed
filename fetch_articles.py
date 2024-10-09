from market_feed.news import fetch_news
from market_feed.utils.json_utils import save_to_json


def main():
    token_address = {"ethereum": "0xbdc7c08592ee4aa51d06c27ee23d5087d65adbcd"}
    token_name = "Lift Dollar"
    token_symbol = "USDL"
    additional_phrases = ["stablecoin"]

    news_articles = fetch_news(
        token_address, token_name, token_symbol, additional_phrases
    )
    save_to_json(news_articles, "usdl_stablecoin_news.json")
    print(
        f"Fetched {len(news_articles)} unique articles about {token_name} ({token_symbol}) with additional phrases: {', '.join(additional_phrases)}"
    )


if __name__ == "__main__":
    main()
