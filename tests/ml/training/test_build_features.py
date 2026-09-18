import pandas as pd
import pytest

from ml.training.build_features import compute_features


def build_test_price_history(num_days: int = 50) -> pd.DataFrame:
    """Builds a minimal, predictable price history for one ticker, for testing.

    num_days must be large enough that at least one row survives dropna():
    it needs >= 20 days of past history (for volatility_20d) AND >= 20 days
    of future data (for target_volatility_20d), so at least ~41 days total.
    """
    dates = pd.date_range(start="2026-01-01", periods=num_days, freq="D")
    prices = [100 + i for i in range(num_days)]

    return pd.DataFrame({
        "date": dates,
        "ticker": "TEST.PA",
        "close_price_eur": prices,
        "volume": [1000] * num_days,
    })


def test_compute_features_returns_non_empty_result():
    """Guards against silently dropping all rows (e.g. if test data is too short)."""
    df = build_test_price_history()
    result = compute_features(df)

    assert len(result) > 0


def test_compute_features_no_null_values():
    df = build_test_price_history()
    result = compute_features(df)

    assert result.isnull().sum().sum() == 0


def test_compute_features_correct_return_value():
    """Prices increase by 1 each day, so return at day t = 1 / price(t-1)."""
    df = build_test_price_history()
    result = compute_features(df)

    row = result[result["date"] == "2026-01-26"].iloc[0]
    expected_return = 1 / 124  # price went from 124 (day 25) to 125 (day 26)

    assert row["return"] == pytest.approx(expected_return)