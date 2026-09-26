"""Lazy model loading: downloads trained volatility models from GCS on
first use, then caches them (on local disk, and in memory for the life
of the running process) so subsequent calls don't re-download."""

import os

import joblib
from google.cloud import storage

from core.config import MODEL_BUCKET, MODEL_DIR, PROJECT_ID

_models: dict[str, object] = {}


def get_model(name: str):
    """Returns a trained model by filename (e.g. 'lightgbm_5d.pkl'),
    downloading it from GCS on first use if not already present locally."""
    if name in _models:
        return _models[name]

    local_path = f"{MODEL_DIR}/{name}"
    if not os.path.exists(local_path):
        _download_model(name, local_path)

    _models[name] = joblib.load(local_path)
    return _models[name]


def _download_model(name: str, local_path: str) -> None:
    """Downloads one model file from the models GCS bucket to local_path."""
    os.makedirs(MODEL_DIR, exist_ok=True)
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(MODEL_BUCKET)
    bucket.blob(name).download_to_filename(local_path)
