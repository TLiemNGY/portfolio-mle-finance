from unittest.mock import patch

from ingestion.streaming.fetch_market_prices import (
    build_prices_dataframe,
    fetch_current_price,
)


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


def test_fetch_current_price_prefers_current_price():
    with patch("ingestion.streaming.fetch_market_prices.yf.Ticker") as mock_ticker:
        mock_ticker.return_value.info = {
            "currentPrice": 379.5,
            "regularMarketPrice": 378.0,
        }
        price = fetch_current_price("MC.PA")

    assert price == 379.5


def test_fetch_current_price_falls_back_to_regular_market_price_for_etfs():
    with patch("ingestion.streaming.fetch_market_prices.yf.Ticker") as mock_ticker:
        mock_ticker.return_value.info = {"regularMarketPrice": 45.2}
        price = fetch_current_price("ESE.PA")

    assert price == 45.2


def test_fetch_current_price_returns_none_without_any_price_field():
    with patch("ingestion.streaming.fetch_market_prices.yf.Ticker") as mock_ticker:
        mock_ticker.return_value.info = {}
        price = fetch_current_price("XXX.PA")

    assert price is None
