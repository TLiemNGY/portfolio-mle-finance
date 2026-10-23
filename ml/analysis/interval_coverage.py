"""Empirical coverage of the price ranges shown by the volatility tool.

The tool turns a daily volatility forecast into price ranges, last close
+/- k * daily_volatility * sqrt(horizon), labelled with normal coverages
(68 % at k=1, 95 % at k=2). This script replays that rule on the test period
(days the evaluated models never saw) and measures how often the price
`horizon` trading days later actually fell inside the range.

Models are refitted on the training period only, exactly as in
ml/training/train.py: the production models (train_final_models.py) are
trained on all the data, test period included, and would look too good here.
"""

import logging

import numpy as np
import pandas as pd
from google.cloud import bigquery
from lightgbm import LGBMRegressor

from core.config import FEATURE_COLUMNS, PROJECT_ID
from ml.training.build_features import compute_features, get_price_history
from ml.training.split import compute_cutoff_date, train_test_split_with_purge

logger = logging.getLogger(__name__)

HORIZONS = (5, 10, 20)
# Must match train_final_models.MODEL_HORIZONS: other horizons use persistence (ADR-010).
LIGHTGBM_HORIZONS = (5, 10)
# Must match agents/tools/volatility_tools.NORMAL_COVERAGE.
NORMAL_COVERAGE = {1: 0.68, 2: 0.95}


def add_future_returns(
    df: pd.DataFrame, horizons: tuple[int, ...] = HORIZONS
) -> pd.DataFrame:
    """Add the realized return between each close and the close `horizon` trading days later.

    Must run before compute_features: its final dropna removes the last rows
    of each ticker, which are needed to know the future of the rows it keeps.
    """
    close_by_ticker = df.groupby("ticker")["close_price_eur"]
    for horizon in horizons:
        df[f"future_return_{horizon}d"] = (
            close_by_ticker.shift(-horizon) / df["close_price_eur"] - 1
        )
    return df


def predict_daily_volatility(
    train: pd.DataFrame, test: pd.DataFrame, horizon: int
) -> pd.Series:
    """Forecast the daily volatility of the test rows, as the tool would.

    LightGBM (same settings as train.py) for the horizons it is used for,
    persistence (the trailing volatility of the same length) otherwise.
    """
    if horizon not in LIGHTGBM_HORIZONS:
        return test[f"volatility_{horizon}d"]

    model = LGBMRegressor(random_state=42)
    model.fit(train[FEATURE_COLUMNS], train[f"target_volatility_{horizon}d"])
    return pd.Series(model.predict(test[FEATURE_COLUMNS]), index=test.index)


def compute_coverage(
    future_return: pd.Series, horizon_volatility: pd.Series
) -> dict[int, float]:
    """Share of days whose return over the horizon ended within +/- k horizon volatilities.

    Args:
        future_return: Realized return over the horizon, one value per day.
        horizon_volatility: Forecast volatility over the same horizon, aligned
            on the same index.

    Returns:
        For each k in NORMAL_COVERAGE, the observed share of days with
        |future_return| <= k * horizon_volatility, e.g. {1: 0.74, 2: 0.92}.
    """
    return {
        k: (future_return.abs() <= k * horizon_volatility).mean()
        for k in NORMAL_COVERAGE
    }


def build_coverage_table(df: pd.DataFrame) -> pd.DataFrame:
    """Replay the tool's ranges on the test period, for each horizon."""
    cutoff = compute_cutoff_date(df)
    rows = []
    for horizon in HORIZONS:
        train, test = train_test_split_with_purge(df, cutoff, purge_days=horizon)
        horizon_volatility = predict_daily_volatility(train, test, horizon) * np.sqrt(
            horizon
        )
        coverage = compute_coverage(
            test[f"future_return_{horizon}d"], horizon_volatility
        )
        rows.append(
            {
                "horizon_days": horizon,
                "method": "lightgbm" if horizon in LIGHTGBM_HORIZONS else "persistence",
                "n_days": len(test),
                "mean_horizon_volatility": horizon_volatility.mean(),
                "expected_1sd": NORMAL_COVERAGE[1],
                "observed_1sd": coverage[1],
                "expected_2sd": NORMAL_COVERAGE[2],
                "observed_2sd": coverage[2],
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    client = bigquery.Client(project=PROJECT_ID)
    df = get_price_history(client)
    df = add_future_returns(df)
    df = compute_features(df)

    table = build_coverage_table(df)
    logger.info(
        "Coverage of the price ranges on the test period (from %s):\n%s",
        compute_cutoff_date(df).date(),
        table.round(3).to_string(index=False),
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )
    main()
