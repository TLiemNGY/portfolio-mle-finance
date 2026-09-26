import logging
from typing import Literal

import pandas as pd
from google.cloud import bigquery

from core.config import DATASET, PROJECT_ID

logger = logging.getLogger(__name__)


def get_portfolio_tickers(client: bigquery.Client) -> list[str]:
    """Returns the distinct list of tickers currently held in the portfolio."""
    query = f"SELECT DISTINCT ticker FROM `{PROJECT_ID}.{DATASET}.portfolio`"
    results = client.query(query).result()
    return [row["ticker"] for row in results]


def load_dataframe_into_bq(
    client: bigquery.Client,
    df: pd.DataFrame,
    table_destination: str,
    write_disposition: Literal["WRITE_APPEND", "WRITE_TRUNCATE"],
) -> None:
    """Loads a DataFrame into a BigQuery table, with the given write disposition."""
    table_id = f"{PROJECT_ID}.{DATASET}.{table_destination}"
    job_config = bigquery.LoadJobConfig(write_disposition=write_disposition)
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    logger.info(f"{len(df)} rows loaded into {table_id}")
