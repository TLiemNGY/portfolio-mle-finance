import numpy as np
import pandas as pd
import pytest

from ml.analysis.return_distribution import compute_return_stats, standardize_returns


def test_compute_return_stats_gives_one_row_per_ticker_and_ignores_missing_returns():
    df = pd.DataFrame(
        {
            "ticker": ["AAA"] * 6 + ["BBB"] * 4,
            "return": [np.nan, -0.02, -0.01, 0.0, 0.01, 0.02, np.nan, 0.01, 0.01, 0.04],
        }
    )

    stats = compute_return_stats(df)

    assert list(stats.columns) == ["n_days", "std", "skew", "excess_kurtosis"]
    assert stats.loc["AAA", "n_days"] == 5
    assert stats.loc["AAA", "std"] == pytest.approx(0.015811, abs=1e-6)
    assert stats.loc["AAA", "skew"] == pytest.approx(0.0, abs=1e-9)
    assert stats.loc["AAA", "excess_kurtosis"] == pytest.approx(-1.2)
    assert stats.loc["BBB", "skew"] == pytest.approx(1.732051, abs=1e-6)
    assert np.isnan(stats.loc["BBB", "excess_kurtosis"])


def test_standardize_returns_uses_the_previous_day_volatility_within_each_ticker():
    df = pd.DataFrame(
        {
            "ticker": ["AAA"] * 3 + ["BBB"] * 2,
            "return": [0.01, 0.02, -0.03, 0.04, 0.02],
            "volatility_20d": [0.01, 0.02, 0.04, 0.02, 0.01],
        }
    )

    result = standardize_returns(df)

    # Previous day's volatility: 0.02 / 0.01 and -0.03 / 0.02.
    assert result["z_conditional"].tolist()[1:3] == pytest.approx([2.0, -1.5])
    # The first day of each ticker has no previous volatility: BBB must not
    # reuse the last volatility of AAA.
    assert np.isnan(result.loc[0, "z_conditional"])
    assert np.isnan(result.loc[3, "z_conditional"])
    assert result.loc[4, "z_conditional"] == pytest.approx(1.0)
    # BBB returns [0.04, 0.02] have a standard deviation of 0.01414.
    assert result.loc[3, "z_unconditional"] == pytest.approx(2.828427, abs=1e-6)
