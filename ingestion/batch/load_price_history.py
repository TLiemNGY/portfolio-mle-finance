import logging

import pandas as pd
import yfinance as yf
from google.cloud import bigquery

from ingestion.common import get_portfolio_tickers, load_dataframe_into_bq

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

PROJECT_ID = "portfolio-mle-finance"
DATASET = "finance_data"


def download_tickers_price_history(client: bigquery.Client) -> pd.DataFrame:
    tickers = get_portfolio_tickers(client)
    history_frames = []

    for ticker in tickers:
        try:
            df_ticker = yf.Ticker(ticker).history(period="2y")
            df_ticker = df_ticker.reset_index()
            df_ticker = df_ticker[["Date", "Close", "Volume"]].rename(
                columns={"Date": "date", "Close": "close_price_eur", "Volume": "volume"}
            )
            df_ticker["ticker"] = ticker
            history_frames.append(df_ticker)
        except Exception as e:  # noqa: BLE001 — intentional catch-all: a single ticker failure must not stop the batch
            logger.error(f"Failed to fetch current price history for {ticker}: {e}")

    if not history_frames:
        return pd.DataFrame()

    return pd.concat(history_frames)


def load_tickers_price_history(client: bigquery.Client, df: pd.DataFrame) -> None:
    load_dataframe_into_bq(client, df, "price_history", "WRITE_TRUNCATE")


def main() -> None:
    client = bigquery.Client(project=PROJECT_ID)
    df = download_tickers_price_history(client)

    if df.empty:
        logger.info("No price history rows loaded, nothing to load.")
        return

    load_tickers_price_history(client, df)


if __name__ == "__main__":
    main()
