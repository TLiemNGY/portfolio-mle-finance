"""Trains final LightGBM models on all available data and persists them to disk."""

import joblib
from google.cloud import bigquery
from lightgbm import LGBMRegressor

from ml.training.build_features import (
    add_targets,
    compute_return_and_volatility_features,
    get_price_history,
)

PROJECT_ID = "portfolio-mle-finance"
FEATURE_COLUMNS = ["volatility_5d", "volatility_10d", "volatility_20d", "volume"]
MODEL_HORIZONS = [
    5,
    10,
]  # LightGBM only beats the persistence baseline at these horizons (see ADR-010)


def main() -> None:
    client = bigquery.Client(project=PROJECT_ID)
    df = get_price_history(client)
    df = compute_return_and_volatility_features(df)
    df = add_targets(df)
    df = df.dropna()

    for horizon in MODEL_HORIZONS:
        target_column = f"target_volatility_{horizon}d"
        model = LGBMRegressor(random_state=42)
        model.fit(df[FEATURE_COLUMNS], df[target_column])

        model_path = f"ml/models/lightgbm_{horizon}d.pkl"
        joblib.dump(model, model_path)
        print(f"Saved model for {horizon}-day horizon to {model_path}")


if __name__ == "__main__":
    main()
