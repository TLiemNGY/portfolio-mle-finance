from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from agents.tools.volatility_tools import get_volatility_forecast
from ml.training.build_features import compute_return_and_volatility_features


def build_test_price_history(num_days: int = 30) -> pd.DataFrame:
    """Builds a minimal, varied price history — enough for a 20-day rolling window."""
    dates = pd.date_range(start="2026-01-01", periods=num_days, freq="D")
    prices = [
        100 + i + (i % 3) for i in range(num_days)
    ]  # slight variation, avoids zero volatility

    return pd.DataFrame(
        {
            "date": dates,
            "ticker": "MC.PA",
            "close_price_eur": prices,
            "volume": [1000] * num_days,
        }
    )


def test_get_volatility_forecast_ticker_not_found():
    with patch("agents.tools.volatility_tools.client") as mock_client:
        mock_client.query.return_value.to_dataframe.return_value = pd.DataFrame()
        result = get_volatility_forecast.func("BAD.PA", 5)

    assert result["method"] == "error"
    assert result["forecast"] is None
    assert "BAD.PA" in result["error"]


def test_get_volatility_forecast_5d_uses_lightgbm():
    df = build_test_price_history()
    fake_model = MagicMock()
    fake_model.predict.return_value = np.array([0.05])

    with (
        patch("agents.tools.volatility_tools.client") as mock_client,
        patch("agents.tools.volatility_tools.joblib.load", return_value=fake_model),
    ):
        mock_client.query.return_value.to_dataframe.return_value = df
        result = get_volatility_forecast.func("MC.PA", 5)

    assert result["method"] == "LGBM"
    assert result["forecast"] == pytest.approx(0.05)
    assert result["forecast_pct"] == "5.00%"
    fake_model.predict.assert_called_once()


def test_get_volatility_forecast_20d_uses_persistence_without_loading_model():
    df = build_test_price_history()
    expected_row = compute_return_and_volatility_features(df.copy()).iloc[-1]

    with (
        patch("agents.tools.volatility_tools.client") as mock_client,
        patch("agents.tools.volatility_tools.joblib.load") as mock_load,
    ):
        mock_client.query.return_value.to_dataframe.return_value = df
        result = get_volatility_forecast.func("MC.PA", 20)

    assert result["method"] == "persistence"
    assert result["forecast"] == pytest.approx(expected_row["volatility_20d"])
    mock_load.assert_not_called()


def test_get_volatility_forecast_invalid_horizon_raises():
    df = build_test_price_history()

    with patch("agents.tools.volatility_tools.client") as mock_client:
        mock_client.query.return_value.to_dataframe.return_value = df
        with pytest.raises(ValueError):
            get_volatility_forecast.func("MC.PA", 15)
