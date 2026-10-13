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
    mock_client = MagicMock()
    mock_client.query.return_value.to_dataframe.return_value = pd.DataFrame()

    with patch("agents.tools.volatility_tools.get_client", return_value=mock_client):
        content, artifact = get_volatility_forecast.func("BAD.PA", 5)

    assert artifact is None
    assert "BAD.PA" in content


@pytest.mark.parametrize(
    (
        "horizon_days",
        "predicted_volatility",
        "expected_horizon_volatility",
        "expected_low_price",
    ),
    [
        (5, 0.05, 0.1118, 116.35),
        (10, 0.03, 0.0949, 118.57),
    ],
)
def test_get_volatility_forecast_uses_lightgbm(
    horizon_days, predicted_volatility, expected_horizon_volatility, expected_low_price
):
    df = build_test_price_history()
    fake_model = MagicMock()
    fake_model.predict.return_value = np.array([predicted_volatility])

    mock_client = MagicMock()
    mock_client.query.return_value.to_dataframe.return_value = df

    with (
        patch("agents.tools.volatility_tools.get_client", return_value=mock_client),
        patch("agents.tools.volatility_tools.get_model", return_value=fake_model),
    ):
        _, artifact = get_volatility_forecast.func("MC.PA", horizon_days)

    assert artifact["method"] == "LGBM"
    assert artifact["daily_volatility"] == pytest.approx(predicted_volatility)
    assert artifact["horizon_volatility"] == pytest.approx(
        expected_horizon_volatility, abs=1e-4
    )
    assert artifact["ranges"][0]["std_devs"] == 1
    assert artifact["ranges"][0]["low_price"] == pytest.approx(
        expected_low_price, abs=0.01
    )

    fake_model.predict.assert_called_once()


def test_get_volatility_forecast_20d_uses_persistence_without_loading_model():
    df = build_test_price_history()
    expected_row = compute_return_and_volatility_features(df.copy()).iloc[-1]

    mock_client = MagicMock()
    mock_client.query.return_value.to_dataframe.return_value = df

    with (
        patch("agents.tools.volatility_tools.get_client", return_value=mock_client),
        patch("agents.tools.volatility_tools.get_model") as mock_get_model,
    ):
        _, artifact = get_volatility_forecast.func("MC.PA", 20)

    assert artifact["method"] == "persistence"
    assert artifact["daily_volatility"] == pytest.approx(expected_row["volatility_20d"])
    mock_get_model.assert_not_called()


def test_get_volatility_forecast_invalid_horizon_raises():
    df = build_test_price_history()

    mock_client = MagicMock()
    mock_client.query.return_value.to_dataframe.return_value = df

    with (
        patch("agents.tools.volatility_tools.get_client", return_value=mock_client),
        pytest.raises(ValueError),
    ):
        get_volatility_forecast.func("MC.PA", 15)
