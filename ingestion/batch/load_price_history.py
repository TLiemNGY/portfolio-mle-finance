import pandas as pd
import yfinance as yf
from google.cloud import bigquery

from ingestion.common import get_portfolio_tickers

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
            print(f"Failed to fetch current price history for {ticker}: {e}")

    if not history_frames:
        return pd.DataFrame()

    return pd.concat(history_frames)


def load_tickers_price_history(client: bigquery.Client, df: pd.DataFrame) -> None:
    table_id = f"{PROJECT_ID}.{DATASET}.price_history"
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    print(f"{len(df)} price history rows loaded into {table_id}")


def main() -> None:
    client = bigquery.Client(project=PROJECT_ID)
    df = download_tickers_price_history(client)

    if df.empty:
        print("No price history rows loaded, nothing to load.")
        return

    load_tickers_price_history(client, df)


if __name__ == "__main__":
    main()
