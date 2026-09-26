"""Chronological train/test split with purge gap to prevent target leakage."""

import logging

import pandas as pd

logger = logging.getLogger(__name__)

TARGET_HORIZON_DAYS = 5  # must match the shift() used to build target_volatility_5d


def compute_cutoff_date(df: pd.DataFrame, test_fraction: float = 0.2) -> pd.Timestamp:
    """Computes the date below which ~test_fraction of the most recent rows fall."""
    return df["date"].quantile(1 - test_fraction)


def train_test_split_with_purge(
    df: pd.DataFrame, cutoff_date: pd.Timestamp, purge_days: int = TARGET_HORIZON_DAYS
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Splits the dataset chronologically into train/test sets.

    Rows whose target window (purge_days ahead) would overlap the test
    period are dropped entirely, to prevent the target from leaking
    information about the test period into the training set.
    """
    purge_start = cutoff_date - pd.Timedelta(days=purge_days)

    train = df[df["date"] < purge_start]
    test = df[df["date"] >= cutoff_date]

    return train, test


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )
    from google.cloud import bigquery

    from config import PROJECT_ID
    from ml.training.build_features import compute_features, get_price_history

    df = get_price_history(client=bigquery.Client(project=PROJECT_ID))
    df = compute_features(df)

    cutoff = compute_cutoff_date(df)
    train, test = train_test_split_with_purge(df, cutoff)

    logger.info(f"Cutoff date: {cutoff}")
    logger.info(
        f"Train: {train.shape[0]} rows ({train['date'].min()} → {train['date'].max()})"
    )
    logger.info(
        f"Test:  {test.shape[0]} rows ({test['date'].min()} → {test['date'].max()})"
    )
