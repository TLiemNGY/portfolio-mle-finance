import logging
import os
from datetime import UTC, datetime

import pandas as pd
import requests
from dotenv import load_dotenv
from google.cloud import bigquery

from config import PROJECT_ID
from ingestion.common import get_portfolio_tickers, load_dataframe_into_bq

load_dotenv()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)
url = "https://api.marketaux.com/v1/news/all"


def get_ticker_news_sentiment(client: bigquery.Client) -> pd.DataFrame:
    """Fetches news sentiment articles linked to portfolio tickers (excluding ETFs)."""
    fetched_at = datetime.now(UTC)
    rows = []
    params = {
        "symbols": "",
        "filter_entities": "true",
        "language": "en",
        "api_token": os.environ["MARKETAUX_API_KEY"],
    }

    tickers = get_portfolio_tickers(client)

    for ticker in tickers:
        if ticker in {"ESE.PA", "PE500.PA"}:
            logger.info(f"Skipping {ticker}: ETFs are not currently supported.")
            continue
        params["symbols"] = ticker
        try:
            response = requests.get(url, params=params)
            data = response.json()
        except Exception as e:  # noqa: BLE001 — intentional catch-all: a single ticker failure must not stop the batch
            logger.error(f"Failed to fetch news articles for {ticker}: {e}")
            continue

        for article in data["data"]:
            if article["entities"]:
                for entity in article["entities"]:
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

    return pd.DataFrame(rows)


def main() -> None:
    client = bigquery.Client(project=PROJECT_ID)
    df = get_ticker_news_sentiment(client)

    if df.empty:
        logger.info("No news articles found. Nothing to load.")
        return

    load_dataframe_into_bq(client, df, "news_sentiment", "WRITE_APPEND")


if __name__ == "__main__":
    main()
