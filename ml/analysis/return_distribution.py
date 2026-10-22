"""Distribution of daily returns: how far are they from a normal distribution?

The volatility tool builds price ranges as last close +/- k standard deviations,
with coverages taken from the normal distribution (68 % at 1 sigma, 95 % at
2 sigma). This analysis checks that assumption on the price history.

Statistics are computed per ticker: pooling tickers with different volatility
levels would create fat tails that do not exist in any single ticker.
"""

import logging

import pandas as pd
from google.cloud import bigquery

from core.config import PROJECT_ID
from ml.training.build_features import (
    compute_return_and_volatility_features,
    get_price_history,
)

logger = logging.getLogger(__name__)


def compute_return_stats(df: pd.DataFrame, column: str = "return") -> pd.DataFrame:
    """Compute the shape statistics of a return column, per ticker.

    Args:
        df: One row per ticker and day, with a "ticker" column and the column
            to describe.
        column: The return column to describe (raw or standardized).

    Returns:
        One row per ticker (index: ticker) with the columns n_days, std, skew
        and excess_kurtosis. Excess kurtosis is 0 for a normal distribution and
        positive for fat tails.
    """
    stats = df.groupby("ticker")[column].agg(["count", "std", "skew", pd.Series.kurt])
    return stats.rename(columns={"count": "n_days", "kurt": "excess_kurtosis"})


def standardize_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Add daily returns expressed in numbers of standard deviations.

    - z_unconditional: return divided by the ticker's standard deviation over
      the whole history (how extreme the day was on average).
    - z_conditional: return divided by the previous day's 20-day volatility,
      i.e. the volatility known before the return happened (how extreme the
      day was given recent conditions). Using the same day's volatility would
      leak the return into its own denominator and hide fat tails.

    Args:
        df: One row per ticker and day, sorted by ticker and date, with the
            columns "ticker", "return" and "volatility_20d".

    Returns:
        The same DataFrame with the columns z_unconditional and z_conditional.
    """
    by_ticker = df.groupby("ticker")
    df["z_unconditional"] = df["return"] / by_ticker["return"].transform("std")
    df["z_conditional"] = df["return"] / by_ticker["volatility_20d"].shift(1)

    return df


def main() -> None:
    client = bigquery.Client(project=PROJECT_ID)
    df = get_price_history(client)
    df = compute_return_and_volatility_features(df)
    df = standardize_returns(df)

    raw = compute_return_stats(df)
    conditional = compute_return_stats(df, column="z_conditional")
    comparison = pd.DataFrame(
        {
            "kurtosis_raw": raw["excess_kurtosis"],
            "kurtosis_conditional": conditional["excess_kurtosis"],
            "std_conditional": conditional["std"],
        }
    ).sort_values("kurtosis_raw", ascending=False)
    logger.info(
        "Excess kurtosis per ticker, raw vs conditional:\n%s",
        comparison.round(3).to_string(),
    )

    pooled = df[["z_unconditional", "z_conditional"]].agg(
        ["count", "std", "skew", pd.Series.kurt]
    )
    logger.info("All tickers pooled:\n%s", pooled.round(3).to_string())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
