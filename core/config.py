"""Centralized project configuration."""

import os

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "portfolio-mle-finance")
DATASET = os.environ.get("DATASET", "finance_data")

FEATURE_COLUMNS = ["volatility_5d", "volatility_10d", "volatility_20d", "volume"]
MODEL_DIR = "ml/models"
MODEL_BUCKET = os.environ.get("MODEL_BUCKET", "portfolio-mle-finance-models")
