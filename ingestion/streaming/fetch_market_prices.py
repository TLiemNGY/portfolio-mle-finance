"""Fetches current market prices for portfolio tickers and appends them to BigQuery."""

from datetime import datetime, timezone

import pandas as pd
import yfinance as yf
from google.cloud import bigquery

PROJECT_ID = "portfolio-mle-finance"
DATASET = "finance_data"


def get_portfolio_tickers(client: bigquery.Client) -> list[str]:
    """Returns the distinct list of tickers currently held in the portfolio."""
    query = f"SELECT DISTINCT ticker FROM `{PROJECT_ID}.{DATASET}.portfolio`"
    results = client.query(query).result()
    return [row["ticker"] for row in results]


def fetch_current_price(ticker: str) -> float | None:
    """Fetches the current price for a single ticker via Yahoo Finance.

    Returns None if the price could not be fetched, instead of raising,
    so that one failing ticker does not stop the whole batch.
    """
    try:
        return yf.Ticker(ticker).info["currentPrice"]
    except Exception as e:
        print(f"Failed to fetch current price for {ticker}: {e}")
        return None


def build_prices_dataframe(tickers: list[str]) -> pd.DataFrame:
    """Fetches prices for all given tickers and returns a DataFrame ready for loading."""
    fetched_at = datetime.now(timezone.utc)
    rows = []
    for ticker in tickers:
        price = fetch_current_price(ticker)
        if pd.notna(price):
            rows.append({"ticker": ticker, "price_eur": price, "fetched_at": fetched_at})
    return pd.DataFrame(rows)


def load_prices(client: bigquery.Client, df: pd.DataFrame) -> None:
    """Appends fetched prices to the market_prices table (never overwrites history)."""
    table_id = f"{PROJECT_ID}.{DATASET}.market_prices"
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    print(f"{len(df)} price rows loaded into {table_id}")


def main() -> None:
    client = bigquery.Client(project=PROJECT_ID)
    tickers = get_portfolio_tickers(client)
    prices_df = build_prices_dataframe(tickers)

    if prices_df.empty:
        print("No prices fetched, nothing to load.")
        return

    load_prices(client, prices_df)


if __name__ == "__main__":
    main()