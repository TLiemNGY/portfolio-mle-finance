"""Fetches news articles and their per-ticker sentiment from Marketaux, and
appends them to BigQuery.

The table is append-only: each weekly run adds the articles it fetched, with
their `fetched_at` timestamp. Articles fetched again on later runs are
deduplicated at read time (see agents/tools/news_tools.py), which keeps the
raw history of every fetch.
"""

import logging
import os
from datetime import UTC, datetime

import pandas as pd
import requests
from dotenv import load_dotenv
from google.cloud import bigquery

from core.config import PROJECT_ID
from ingestion.common import get_portfolio_tickers, load_dataframe_into_bq

load_dotenv()
logger = logging.getLogger(__name__)

MARKETAUX_URL = "https://api.marketaux.com/v1/news/all"
REQUEST_TIMEOUT_SECONDS = 30
# ETFs are not covered by Marketaux: no request is made for them.
UNSUPPORTED_TICKERS = {"ESE.PA", "PE500.PA"}


def fetch_articles(ticker: str, api_token: str) -> list[dict]:
    """Returns the raw Marketaux articles for one ticker.

    Raises requests.RequestException on a network error, a timeout, an HTTP
    error (e.g. 402 when the daily quota is exhausted) or an invalid JSON
    body, and KeyError if the response has no "data" field.
    """
    response = requests.get(
        MARKETAUX_URL,
        params={
            "symbols": ticker,
            "filter_entities": "true",
            "language": "en",
            "api_token": api_token,
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()["data"]


def articles_to_rows(articles: list[dict], fetched_at: datetime) -> list[dict]:
    """Flattens Marketaux articles into one row per (article, entity)."""
    rows = []
    for article in articles:
        for entity in article.get("entities") or []:
            rows.append(
                {
                    "ticker": entity["symbol"],
                    "title": article["title"],
                    "description": article["description"],
                    "url": article["url"],
                    "source": article["source"],
                    "published_at": article["published_at"],
                    "sentiment_score": entity["sentiment_score"],
                    "match_score": entity["match_score"],
                    "fetched_at": fetched_at,
                }
            )
    return rows


def get_ticker_news_sentiment(client: bigquery.Client) -> pd.DataFrame:
    """Fetches news articles for the portfolio tickers, skipping unsupported ones.

    A failing ticker is logged and skipped, so that it does not stop the batch.
    """
    api_token = os.environ["MARKETAUX_API_KEY"]
    fetched_at = datetime.now(UTC)
    rows = []

    for ticker in get_portfolio_tickers(client):
        if ticker in UNSUPPORTED_TICKERS:
            logger.info("Skipping %s: not covered by Marketaux.", ticker)
            continue
        try:
            articles = fetch_articles(ticker, api_token)
        except (requests.RequestException, KeyError) as error:
            logger.error("Failed to fetch news for %s: %s", ticker, error)
            continue
        rows.extend(articles_to_rows(articles, fetched_at))

    return pd.DataFrame(rows)


def main() -> None:
    client = bigquery.Client(project=PROJECT_ID)
    df = get_ticker_news_sentiment(client)

    if df.empty:
        logger.info("No news articles found. Nothing to load.")
        return

    load_dataframe_into_bq(client, df, "news_sentiment", "WRITE_APPEND")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )
    main()
