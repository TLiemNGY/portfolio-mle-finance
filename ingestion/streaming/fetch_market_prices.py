"""Fetches current market prices for portfolio tickers and appends them to BigQuery."""

import logging
from datetime import UTC, datetime

import pandas as pd
import yfinance as yf
from google.cloud import bigquery

from core.config import PROJECT_ID
from ingestion.common import get_portfolio_tickers, load_dataframe_into_bq

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def fetch_current_price(ticker: str) -> float | None:
    """Fetches the current price for a single ticker via Yahoo Finance.

    Returns None if the price could not be fetched, instead of raising,
    so that one failing ticker does not stop the whole batch.
    """
    try:
        return yf.Ticker(ticker).info["currentPrice"]
    except Exception as e:  # noqa: BLE001 — intentional catch-all: a single ticker failure must not stop the batch
        logger.error(f"Failed to fetch current price for {ticker}: {e}")
        return None


def build_prices_dataframe(tickers: list[str]) -> pd.DataFrame:
    """Fetches prices for all given tickers and returns a DataFrame ready for loading."""
    fetched_at = datetime.now(UTC)
    rows = []
    for ticker in tickers:
        price = fetch_current_price(ticker)
        if pd.notna(price):
            rows.append(
                {"ticker": ticker, "price_eur": price, "fetched_at": fetched_at}
            )
    return pd.DataFrame(rows)


def main() -> None:
    client = bigquery.Client(project=PROJECT_ID)
    tickers = get_portfolio_tickers(client)
    prices_df = build_prices_dataframe(tickers)

    if prices_df.empty:
        logger.info("No prices fetched, nothing to load.")
        return
    load_dataframe_into_bq(client, prices_df, "market_prices", "WRITE_APPEND")


if __name__ == "__main__":
    main()
