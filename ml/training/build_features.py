import pandas as pd
from google.cloud import bigquery

PROJECT_ID = "portfolio-mle-finance"
DATASET = "finance_data"


def get_price_history(client: bigquery.Client) -> pd.DataFrame:
    table_id = f"{PROJECT_ID}.{DATASET}.price_history"
    query = f"""
        SELECT date, close_price_eur, volume, ticker 
        FROM `{table_id}`
        ORDER BY ticker ASC, date ASC
        """
    results = client.query(query)

    return results.to_dataframe()


def verify_gaps_in_data(df: pd.DataFrame) -> None:
    """Prints a diagnostic count of suspicious gaps (>5 days) in the price history per ticker."""
    gaps = df.groupby("ticker")["date"].diff().dt.days
    suspicious_gaps = gaps[gaps > 5].count()
    print(f"{suspicious_gaps} gaps of more than 5 days detected.")


def compute_return_and_volatility_features(df: pd.DataFrame) -> pd.DataFrame:
    """Computes only backward-looking features (safe to use at inference time)."""
    df["return"] = df.groupby("ticker")["close_price_eur"].pct_change()
    df["volatility_5d"] = df.groupby("ticker")["return"].transform(
        lambda x: x.rolling(5).std()
    )
    df["volatility_10d"] = df.groupby("ticker")["return"].transform(
        lambda x: x.rolling(10).std()
    )
    df["volatility_20d"] = df.groupby("ticker")["return"].transform(
        lambda x: x.rolling(20).std()
    )
    return df


def add_targets(df: pd.DataFrame) -> pd.DataFrame:
    """Adds forward-looking target columns (training-only, requires future data)."""
    df["target_volatility_5d"] = df.groupby("ticker")["volatility_5d"].shift(-5)
    df["target_volatility_10d"] = df.groupby("ticker")["volatility_10d"].shift(-10)
    df["target_volatility_20d"] = df.groupby("ticker")["volatility_20d"].shift(-20)
    return df


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """Full pipeline for training: features + targets, dropping incomplete rows."""
    df = compute_return_and_volatility_features(df)
    df = add_targets(df)
    return df.dropna()


if __name__ == "__main__":
    df = get_price_history(client=bigquery.Client(project=PROJECT_ID))
    verify_gaps_in_data(df)
    df = compute_features(df)
    print(df.shape)
    print(df.head())
