"""Fetches recent financial news for portfolio tickers via GDELT and stores them in Cloud Storage."""

from datetime import UTC, datetime

import pandas as pd
import requests
from gdeltdoc import Filters, GdeltDoc
from google.cloud import storage
from tenacity import retry, stop_after_attempt, wait_exponential
from unidecode import unidecode

PROJECT_ID = "portfolio-mle-finance"
BUCKET_NAME = "portfolio-mle-finance-news"

# gdeltdoc doesn't send a User-Agent header, which causes GDELT's API to
# reject requests with a misleading rate-limit error even when no real
# quota has been exceeded (see github.com/alex9smith/gdelt-doc-api/issues/22).
# We patch requests.get globally to always include one.
_original_get = requests.get


def _get_with_user_agent(url, *args, **kwargs):
    headers = kwargs.pop("headers", {}) or {}
    headers.setdefault(
        "User-Agent",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    )
    return _original_get(url, headers=headers, *args, **kwargs)


requests.get = _get_with_user_agent


TICKER_TO_SEARCH_TERM = {
    "MC.PA": "LVMH",
    "OR.PA": "L'Oreal",
    "AI.PA": "Air Liquide",
    "SAN.PA": "Sanofi",
    "BNP.PA": "BNP Paribas",
}


@retry(wait=wait_exponential(multiplier=1, min=30, max=300), stop=stop_after_attempt(5))
def search_all_articles(ticker_to_search_term: dict[str, str]):
    """Searches GDELT once for all tickers combined, using a single OR query."""
    f = Filters(keyword=list(ticker_to_search_term.values()), timespan="1m")
    gd = GdeltDoc()
    return gd.article_search(f)


def attribute_articles(articles_df, ticker_to_search_term: dict[str, str]) -> dict:
    """Splits the combined results back into one DataFrame per ticker."""
    normalized_titles = articles_df["title"].apply(
        lambda title: unidecode(title) if pd.notna(title) else ""
    )

    result = {}
    for ticker, search_term in ticker_to_search_term.items():
        normalized_term = unidecode(search_term)
        mask = normalized_titles.str.contains(normalized_term, case=False, na=False)
        result[ticker] = articles_df[mask]
    return result


def upload_articles(bucket: storage.Bucket, ticker: str, articles_json: str) -> None:
    """Uploads a ticker's articles as a JSON file to Cloud Storage."""
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
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
