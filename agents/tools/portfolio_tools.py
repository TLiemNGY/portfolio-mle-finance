"""BigQuery-backed tools for querying portfolio holdings and market prices."""

from google.cloud import bigquery
from langchain_core.tools import tool

from core.clients import get_client
from core.config import DATASET, PROJECT_ID


@tool
def get_portfolio_summary() -> list[dict]:
    """Fetches a summary of the current portfolio: ticker, name, sector, quantity, and current value."""
    client = get_client()
    query = f"SELECT ticker, name, sector, quantity, current_value_eur FROM `{PROJECT_ID}.{DATASET}.portfolio`"
    results = client.query(query).result()
    return [dict(row) for row in results]


@tool
def get_latest_price(ticker: str) -> dict | None:
    """Returns the most recent recorded market price for a given ticker, or None if not found."""
    client = get_client()
    query = f"""
        SELECT ticker, price_eur, fetched_at
        FROM `{PROJECT_ID}.{DATASET}.market_prices`
        WHERE ticker = @ticker
        ORDER BY fetched_at DESC
        LIMIT 1
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("ticker", "STRING", ticker)]
    )
    results = client.query(query, job_config=job_config).result()
    rows = [dict(row) for row in results]
    return rows[0] if rows else None
