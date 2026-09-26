import pandas as pd

from ml.training.split import train_test_split_with_purge


def test_train_test_split_purges_exact_row_count_per_ticker():
    """Verifies the purge removes exactly purge_days rows per ticker,
    regardless of calendar gaps — this is what the calendar-day bug missed."""
    dates = pd.date_range("2026-01-01", periods=30, freq="D")
    df = pd.DataFrame({"ticker": ["A"] * 30 + ["B"] * 30, "date": list(dates) * 2})

    cutoff = dates[20]
    train, _ = train_test_split_with_purge(df, cutoff, purge_days=5)

    for ticker in ["A", "B"]:
        ticker_dates = train[train["ticker"] == ticker]["date"]
        assert len(ticker_dates) == 15  # 20 rows before cutoff, minus 5 purged
        assert ticker_dates.max() == dates[14]
