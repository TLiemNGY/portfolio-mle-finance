"""BigQuery-backed tool forecasting per-ticker volatility, using cached
models loaded from GCS (see models.py) for the 5/10-day horizons."""

import argparse
import logging
import math

from google.cloud import bigquery
from langchain_core.tools import tool

from core.clients import get_client
from core.config import DATASET, FEATURE_COLUMNS, PROJECT_ID
from core.models import get_model
from ml.training.build_features import compute_return_and_volatility_features

logger = logging.getLogger(__name__)

MODEL_FILES = {5: "lightgbm_5d.pkl", 10: "lightgbm_10d.pkl"}
TRADING_DAYS_PER_YEAR = 252
# Number of standard deviations -> probability that the price stays within
# that range, under a normal approximation (to be calibrated on real data).
NORMAL_COVERAGE = {1: 0.68, 2: 0.95}


def format_volatility_summary(artifact: dict) -> str:
    """Builds the short text summary of a volatility forecast, read by the LLM."""
    one_sd = artifact["ranges"][0]
    two_sd = artifact["ranges"][1]
    return (
        f"{artifact['ticker']}, {artifact['horizon_days']}-day horizon "
        f"({artifact['method']} model), last close {artifact['last_close']:.2f} EUR. "
        f"Normal approximation: ~{one_sd['probability']:.0%} chance the price stays "
        f"within ±{one_sd['high_pct']:.2%} "
        f"({one_sd['low_price']:.2f}–{one_sd['high_price']:.2f} EUR), "
        f"~{two_sd['probability']:.0%} within ±{two_sd['high_pct']:.2%} "
        f"({two_sd['low_price']:.2f}–{two_sd['high_price']:.2f} EUR) "
        f"over the next {artifact['horizon_days']} trading days. "
        f"Based on a daily standard deviation of returns of "
        f"{artifact['daily_volatility']:.2%}. This measures risk, not direction."
    )


@tool(response_format="content_and_artifact")
def get_volatility_forecast(ticker: str, horizon_days: int) -> tuple[str, dict | None]:
    """Forecasts the volatility (risk) of a stock over the next 5, 10 or 20 trading days.

    Use this tool when the user asks about risk, volatility or the expected size
    of price moves for a stock. It does not predict the direction of the price:
    never use it to say whether a stock will go up or down.

    Args:
        ticker: The stock ticker in Euronext Paris format (e.g. "MC.PA" for LVMH,
            "OR.PA" for L'Oreal), NOT the company name.
        horizon_days: Forecast horizon in trading days. One of 5, 10, or 20.
            For "a week" use 5, for "two weeks" use 10, for "a month" use 20.

    Returns:
        A short text summary to base the answer on. The forecast is the daily
        standard deviation of returns (5 and 10 days: LightGBM model; 20 days:
        current realized volatility, i.e. persistence), converted to the
        requested horizon. The summary gives the price ranges at ±1 and ±2
        standard deviations around the last close, in percent and in EUR, with
        their approximate probabilities under a normal approximation (~68% and
        ~95%).
        If no price history exists for the ticker, the summary explains the
        error: ask the user for the correct Euronext ticker.
    """
    if horizon_days not in {5, 10, 20}:
        raise ValueError("Invalid horizon_days")

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
        return (
            f"No price history found for ticker '{ticker}'. Use the Euronext format (e.g. 'MC.PA'), not the company name.",
            None,
        )

    df = compute_return_and_volatility_features(df)
    last_close = float(df["close_price_eur"].iloc[-1])
    df = df[FEATURE_COLUMNS]
    most_recent_row = df.iloc[[-1]]

    if horizon_days == 20:
        daily_volatility = float(most_recent_row["volatility_20d"].iloc[0])
        method = "persistence"
    else:
        model = get_model(MODEL_FILES[horizon_days])
        daily_volatility = float(model.predict(most_recent_row)[0])
        method = "LGBM"

    horizon_volatility = daily_volatility * math.sqrt(horizon_days)
    annualized_volatility = daily_volatility * math.sqrt(TRADING_DAYS_PER_YEAR)

    ranges = []
    for std_devs, probability in NORMAL_COVERAGE.items():
        half_width = std_devs * horizon_volatility
        low_pct = -half_width
        high_pct = half_width
        low_price = last_close * (1 + low_pct)
        high_price = last_close * (1 + high_pct)

        ranges.append(
            {
                "std_devs": std_devs,
                "probability": probability,
                "low_pct": low_pct,
                "high_pct": high_pct,
                "low_price": low_price,
                "high_price": high_price,
            }
        )

    artifact = {
        "ticker": ticker,
        "horizon_days": horizon_days,
        "method": method,
        "last_close": last_close,
        "daily_volatility": daily_volatility,
        "horizon_volatility": horizon_volatility,
        "annualized_volatility": annualized_volatility,
        "ranges": ranges,
    }

    content = format_volatility_summary(artifact)
    return content, artifact


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
