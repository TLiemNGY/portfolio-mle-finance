import pandas as pd
import pytest

from ml.analysis.interval_coverage import add_future_returns, compute_coverage


def test_compute_coverage_counts_returns_within_k_volatilities_bounds_included():
    future_return = pd.Series([0.01, -0.03, 0.05, -0.02])
    horizon_volatility = pd.Series([0.02, 0.02, 0.02, 0.02])

    coverage = compute_coverage(future_return, horizon_volatility)

    # Within 1 sigma (0.02): 0.01 and -0.02 (the bound itself is inside).
    assert coverage[1] == pytest.approx(0.5)
    # Within 2 sigma (0.04): all but 0.05.
    assert coverage[2] == pytest.approx(0.75)


def test_add_future_returns_stays_within_each_ticker():
    df = pd.DataFrame(
        {
            "ticker": ["AAA", "AAA", "AAA", "BBB", "BBB"],
            "close_price_eur": [100.0, 110.0, 121.0, 50.0, 55.0],
        }
    )

    result = add_future_returns(df, horizons=(1,))

    assert result["future_return_1d"].tolist()[:2] == pytest.approx([0.10, 0.10])
    # The last day of AAA has no future: it must not use the first price of BBB.
    assert pd.isna(result.loc[2, "future_return_1d"])
    assert result.loc[3, "future_return_1d"] == pytest.approx(0.10)
