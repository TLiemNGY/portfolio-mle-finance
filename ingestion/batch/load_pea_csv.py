"""Batch ingestion of PEA portfolio CSV files into BigQuery."""

import pandas as pd
from google.cloud import bigquery

PROJECT_ID = "portfolio-mle-finance"
DATASET = "finance_data"

REQUIRED_PORTFOLIO_COLUMNS = {
    "ticker", "name", "sector", "purchase_date", "quantity",
    "purchase_price_eur", "current_price_eur", "invested_value_eur",
    "current_value_eur", "unrealized_pnl_eur", "unrealized_pnl_pct",
    "currency", "account_type",
}


def validate_portfolio(df: pd.DataFrame) -> None:
    """Data contract check: validates the portfolio DataFrame before loading.

    Raises:
        ValueError: if the DataFrame violates any expected invariant.
    """
    missing_columns = REQUIRED_PORTFOLIO_COLUMNS - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing columns: {missing_columns}")

    if df["quantity"].isnull().any():
        raise ValueError("Some rows have a missing quantity")

    if (df["quantity"] <= 0).any():
        raise ValueError("Negative or zero quantity detected")

    if (df["purchase_price_eur"] <= 0).any():
        raise ValueError("Negative or zero purchase price detected")

    print(f"Validation OK — {len(df)} rows conform.")


def load_table(client: bigquery.Client, df: pd.DataFrame, table_name: str) -> None:
    """Loads a DataFrame into a BigQuery table, replacing its content.

    Note: WRITE_TRUNCATE is used for local development convenience only.
    Never use this disposition in production — prefer WRITE_APPEND with
    explicit deduplication logic.
    """
    table_id = f"{PROJECT_ID}.{DATASET}.{table_name}"
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    print(f"{len(df)} rows loaded into {table_id}")


def main() -> None:
    client = bigquery.Client(project=PROJECT_ID)

    portfolio_df = pd.read_csv("data/samples/pea_portfolio.csv", parse_dates=["purchase_date"])
    validate_portfolio(portfolio_df)
    load_table(client, portfolio_df, "portfolio")

    transactions_df = pd.read_csv("data/samples/pea_transactions.csv", parse_dates=["date"])
    load_table(client, transactions_df, "transactions")

    allocation_df = pd.read_csv("data/samples/pea_sector_allocation.csv")
    load_table(client, allocation_df, "sector_allocation")


if __name__ == "__main__":
    main()