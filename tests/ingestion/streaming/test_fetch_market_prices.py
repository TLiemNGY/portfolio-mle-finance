from unittest.mock import patch

from ingestion.streaming.fetch_market_prices import build_prices_dataframe


def test_build_prices_dataframe_skips_failed_or_nan_tickers():
    def fake_fetch(ticker):
        if ticker == "BAD.PA":
            return None
        if ticker == "NAN.PA":
            return float("nan")
        return 100.0

    with patch(
        "ingestion.streaming.fetch_market_prices.fetch_current_price",
        side_effect=fake_fetch,
    ):
        df = build_prices_dataframe(["MC.PA", "BAD.PA", "NAN.PA", "OR.PA"])

    assert len(df) == 2
    assert set(df["ticker"]) == {"MC.PA", "OR.PA"}
