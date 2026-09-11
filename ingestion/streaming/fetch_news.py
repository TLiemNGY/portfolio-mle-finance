"""Fetches recent financial news for portfolio tickers via GDELT and stores them in Cloud Storage."""

from datetime import datetime, timezone

from gdeltdoc import GdeltDoc, Filters
from google.cloud import storage
from tenacity import retry, wait_exponential, stop_after_attempt

PROJECT_ID = "portfolio-mle-finance"
BUCKET_NAME = "portfolio-mle-finance-news"

TICKER_TO_SEARCH_TERM = {
    "MC.PA": "LVMH",
    "OR.PA": "L'Oreal",
    "AI.PA": "Air Liquide",
    "SAN.PA": "Sanofi",
    "BNP.PA": "BNP Paribas",
}


@retry(wait=wait_exponential(multiplier=1, min=30, max=300), stop=stop_after_attempt(5))
def search_all_articles(ticker_to_search_term: dict[str, str]):
    """Searches GDELT once for all tickers combined, using a single OR query.

    Combining tickers into one request minimizes exposure to GDELT's rate
    limit, at the cost of needing to re-attribute results afterwards.
    """
    combined_query = " OR ".join(ticker_to_search_term.values())
    f = Filters(keyword=combined_query, timespan="1m")
    gd = GdeltDoc()
    return gd.article_search(f)


def attribute_articles(articles_df, ticker_to_search_term: dict[str, str]) -> dict:
    """Splits the combined results back into one DataFrame per ticker,
    based on whether the search term appears in the article title.

    Note: an article may be attributed to multiple tickers if it mentions
    several companies, or to none if the term appears in the body but not
    the title (a known limitation of this approach).
    """
    result = {}
    for ticker, search_term in ticker_to_search_term.items():
        mask = articles_df["title"].str.contains(search_term, case=False, na=False)
        result[ticker] = articles_df[mask]
    return result


def upload_articles(bucket: storage.Bucket, ticker: str, articles_json: str) -> None:
    """Uploads a ticker's articles as a JSON file to Cloud Storage."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    file = f"news/{ticker}/{timestamp}.json"
    blob = bucket.blob(file)
    blob.upload_from_string(articles_json, content_type="application/json")
    print(f"Uploaded {file}")


def main() -> None:
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)

    all_articles_df = search_all_articles(TICKER_TO_SEARCH_TERM)

    if all_articles_df.empty:
        print("No articles found for any ticker.")
        return

    articles_by_ticker = attribute_articles(all_articles_df, TICKER_TO_SEARCH_TERM)

    for ticker, ticker_articles_df in articles_by_ticker.items():
        if ticker_articles_df.empty:
            print(f"No articles attributed to {ticker}")
            continue

        articles_json = ticker_articles_df.to_json(orient="records", date_format="iso")
        upload_articles(bucket, ticker, articles_json)


if __name__ == "__main__":
    main()