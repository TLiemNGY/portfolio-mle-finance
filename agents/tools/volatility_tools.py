import argparse
import logging

import joblib
from google.cloud import bigquery
from langchain_core.tools import tool

from clients import get_client
from config import DATASET, FEATURE_COLUMNS, MODEL_DIR, PROJECT_ID
from ml.training.build_features import compute_return_and_volatility_features

logger = logging.getLogger(__name__)


@tool
def get_volatility_forecast(ticker: str, horizon_days: int) -> dict:
    """Forecasts the volatility of a ticker over a given horizon (5, 10, or 20 trading days).

    Args:
        ticker: The stock ticker in Euronext Paris format (e.g. "MC.PA" for LVMH,
            "OR.PA" for L'Oreal), NOT the company name.
        horizon_days: One of 5, 10, or 20.

    For 5 and 10 days, uses a trained LightGBM model. For 20 days, returns
    the current 20-day realized volatility directly (persistence), since no
    trained model outperforms this baseline at that horizon (see ADR-010).

    Returns a dict with:
    - forecast_pct: pre-formatted percentage string, ready to show the user directly
    - forecast: raw decimal value, for any further calculation only
    """
    client = get_client()
    query = f"""
            SELECT ticker, volume, close_price_eur, date
            FROM `{PROJECT_ID}.{DATASET}.price_history`
            WHERE ticker = @ticker
            AND DATE(date) >= current_date() - 60
            ORDER BY date ASC
        """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("ticker", "STRING", ticker)]
    )

    results = client.query(query, job_config=job_config)
    df = results.to_dataframe()

    if df.empty:
        return {
            "ticker": ticker,
            "horizon_days": horizon_days,
            "forecast": None,
            "method": "error",
            "error": f"No price history found for ticker '{ticker}'. Use the Euronext format (e.g. 'MC.PA'), not the company name.",
        }

    df = compute_return_and_volatility_features(df)
    df = df[FEATURE_COLUMNS]
    most_recent_row = df.iloc[[-1]]

    if horizon_days == 5:
        model = joblib.load(f"{MODEL_DIR}/lightgbm_5d.pkl")
        forecast = float(model.predict(most_recent_row)[0])

        return {
            "ticker": ticker,
            "horizon_days": horizon_days,
            "forecast": forecast,
            "forecast_pct": f"{forecast * 100:.2f}%",
            "method": "LGBM",
        }

    elif horizon_days == 10:
        model = joblib.load(f"{MODEL_DIR}/lightgbm_10d.pkl")
        forecast = float(model.predict(most_recent_row)[0])

        return {
            "ticker": ticker,
            "horizon_days": horizon_days,
            "forecast": forecast,
            "forecast_pct": f"{forecast * 100:.2f}%",
            "method": "LGBM",
        }

    elif horizon_days == 20:
        forecast = float(most_recent_row["volatility_20d"].iloc[0])

        return {
            "ticker": ticker,
            "horizon_days": 20,
            "forecast": forecast,
            "forecast_pct": f"{forecast * 100:.2f}%",
            "method": "persistence",
        }
    else:
        raise ValueError("Invalid horizon_days")


def main(ticker, horizon_days):
    return get_volatility_forecast.func(ticker, horizon_days)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", type=str, required=True)
    parser.add_argument("--horizon_days", type=int, required=True)
    args = parser.parse_args()

    result = main(args.ticker, args.horizon_days)
    logger.info(result)
