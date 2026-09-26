"""Trains final LightGBM models on all available data, saves them locally,
and uploads them to GCS so they're accessible from any environment
(e.g. a Cloud Run container, which never has local training artifacts)."""

import logging

import joblib
from google.cloud import bigquery, storage
from lightgbm import LGBMRegressor

from core.config import FEATURE_COLUMNS, MODEL_BUCKET, MODEL_DIR, PROJECT_ID
from ml.training.build_features import (
    add_targets,
    compute_return_and_volatility_features,
    get_price_history,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

MODEL_HORIZONS = [
    5,
    10,
]  # LightGBM only beats the persistence baseline at these horizons (see ADR-010)


def upload_model_to_gcs(local_path: str, blob_name: str) -> None:
    """Uploads a trained model file to the models GCS bucket."""
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(MODEL_BUCKET)
    bucket.blob(blob_name).upload_from_filename(local_path)
    logger.info(f"Uploaded {local_path} to gs://{MODEL_BUCKET}/{blob_name}")


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

        model_path = f"{MODEL_DIR}/lightgbm_{horizon}d.pkl"
        joblib.dump(model, model_path)
        logger.info(f"Saved model for {horizon}-day horizon to {model_path}")

        upload_model_to_gcs(model_path, f"lightgbm_{horizon}d.pkl")


if __name__ == "__main__":
    main()
