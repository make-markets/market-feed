from market_feed.news import fetch_news


def main():
    search_phrase = "USDL Stablecoin"

    news_articles = fetch_news(search_phrase)
    breakpoint()


if __name__ == "__main__":
    main()
