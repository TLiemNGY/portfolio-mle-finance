import os
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
import requests

from ingestion.streaming.fetch_news_sentiment import (
    articles_to_rows,
    fetch_articles,
    get_ticker_news_sentiment,
)

FETCHED_AT = datetime(2026, 10, 22, tzinfo=UTC)


def build_article(symbol: str) -> dict:
    """Builds a minimal Marketaux article with one entity."""
    return {
        "title": f"News on {symbol}",
        "description": "A description.",
        "url": f"https://example.com/{symbol}",
        "source": "example.com",
        "published_at": "2026-10-20T08:00:00Z",
        "entities": [{"symbol": symbol, "sentiment_score": 0.5, "match_score": 10.0}],
    }


def test_articles_to_rows_creates_one_row_per_entity_and_skips_articles_without_entity():
    article_without_entity = {**build_article("MC.PA"), "entities": None}

    rows = articles_to_rows(
        [build_article("MC.PA"), article_without_entity], FETCHED_AT
    )

    assert len(rows) == 1
    assert rows[0]["ticker"] == "MC.PA"
    assert rows[0]["fetched_at"] == FETCHED_AT


def test_fetch_articles_uses_a_timeout_and_raises_on_http_error():
    response = MagicMock()
    response.raise_for_status.side_effect = requests.HTTPError("402 Payment Required")

    with (
        patch(
            "ingestion.streaming.fetch_news_sentiment.requests.get",
            return_value=response,
        ) as mock_get,
        pytest.raises(requests.HTTPError),
    ):
        fetch_articles("MC.PA", api_token="test")

    assert mock_get.call_args.kwargs["timeout"] > 0


def test_a_failing_ticker_does_not_stop_the_batch_and_etfs_are_skipped():
    def fake_fetch(ticker, api_token):
        if ticker == "OR.PA":
            raise requests.Timeout("Marketaux did not answer")
        return [build_article(ticker)]

    with (
        patch.dict(os.environ, {"MARKETAUX_API_KEY": "test"}),
        patch(
            "ingestion.streaming.fetch_news_sentiment.get_portfolio_tickers",
            return_value=["MC.PA", "OR.PA", "ESE.PA", "SAN.PA"],
        ),
        patch(
            "ingestion.streaming.fetch_news_sentiment.fetch_articles",
            side_effect=fake_fetch,
        ) as mock_fetch,
    ):
        df = get_ticker_news_sentiment(client=MagicMock())

    assert set(df["ticker"]) == {"MC.PA", "SAN.PA"}
    fetched_tickers = [call.args[0] for call in mock_fetch.call_args_list]
    assert "ESE.PA" not in fetched_tickers
