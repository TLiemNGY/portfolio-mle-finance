"""Trains and compares baseline and candidate models across multiple volatility horizons."""

import numpy as np
import pandas as pd
from google.cloud import bigquery
from lightgbm import LGBMRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

from ml.training.build_features import compute_features, get_price_history
from ml.training.split import compute_cutoff_date, train_test_split_with_purge

PROJECT_ID = "portfolio-mle-finance"

HORIZONS = {
    5: {"feature": "volatility_5d", "target": "target_volatility_5d"},
    10: {"feature": "volatility_10d", "target": "target_volatility_10d"},
    20: {"feature": "volatility_20d", "target": "target_volatility_20d"},
}
FEATURE_COLUMNS = ["volatility_5d", "volatility_10d", "volatility_20d", "volume"]


def evaluate(y_true: pd.Series, y_pred: np.ndarray, horizon: int, model_name: str) -> dict:
    """Computes MAE and RMSE for a model's predictions, returned as a result row."""
    return {
        "horizon_days": horizon,
        "model": model_name,
        "mae": mean_absolute_error(y_true, y_pred),
        "rmse": root_mean_squared_error(y_true, y_pred),
    }


def run_horizon(train: pd.DataFrame, test: pd.DataFrame, horizon: int, target_column: str) -> list[dict]:
    """Trains and evaluates all models for a single prediction horizon."""
    X_train, y_train = train[FEATURE_COLUMNS], train[target_column]
    X_test, y_test = test[FEATURE_COLUMNS], test[target_column]

    results = []

    mean_prediction = np.full(len(y_test), y_train.mean())
    results.append(evaluate(y_test, mean_prediction, horizon, "baseline_mean"))

    persistence_feature = HORIZONS[horizon]["feature"]
    persistence_prediction = X_test[persistence_feature]
    results.append(evaluate(y_test, persistence_prediction, horizon, "baseline_persistence"))

    linear_model = LinearRegression()
    linear_model.fit(X_train, y_train)
    results.append(evaluate(y_test, linear_model.predict(X_test), horizon, "linear_regression"))

    lgbm_model = LGBMRegressor(random_state=42)
    lgbm_model.fit(X_train, y_train)
    results.append(evaluate(y_test, lgbm_model.predict(X_test), horizon, "lightgbm"))

    return results


def build_results_df() -> pd.DataFrame:
    """Runs the full multi-horizon model comparison and returns the results table."""
    client = bigquery.Client(project=PROJECT_ID)
    df = get_price_history(client)
    df = compute_features(df)

    cutoff = compute_cutoff_date(df)

    all_results = []
    for horizon, columns in HORIZONS.items():
        train, test = train_test_split_with_purge(df, cutoff, purge_days=horizon)
        all_results.extend(run_horizon(train, test, horizon, columns["target"]))

    return pd.DataFrame(all_results).sort_values(["horizon_days", "mae"])


def main() -> None:
    results_df = build_results_df()
    print(results_df)


if __name__ == "__main__":
    main()