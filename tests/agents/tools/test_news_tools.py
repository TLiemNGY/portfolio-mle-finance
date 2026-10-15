from unittest.mock import MagicMock, patch

from agents.tools.news_tools import format_news_summary, get_news_sentiment


def build_article(published_date: str, title: str, sentiment_score) -> dict:
    """Builds one article row, as returned by the BigQuery query."""
    return {
        "title": title,
        "description": f"Description of {title}",
        "url": f"https://example.com/{title}",
        "source": "example.com",
        "published_date": published_date,
        "sentiment_score": sentiment_score,
        "match_score": 10.0,
    }


def test_get_news_sentiment_without_recent_news_returns_no_artifact():
    mock_client = MagicMock()
    mock_client.query.return_value.result.return_value = []

    with patch("agents.tools.news_tools.get_client", return_value=mock_client):
        content, artifact = get_news_sentiment.func("AIR.PA")

    assert artifact is None
    assert "AIR.PA" in content


def test_get_news_sentiment_presents_articles_most_recent_first():
    rows = [
        build_article("2026-09-20", "Older article", 0.3),
        build_article("2026-10-10", "Newer article", -0.2),
    ]
    mock_client = MagicMock()
    mock_client.query.return_value.result.return_value = rows

    with patch("agents.tools.news_tools.get_client", return_value=mock_client):
        content, artifact = get_news_sentiment.func("MC.PA")

    assert [a["title"] for a in artifact["articles"]] == [
        "Newer article",
        "Older article",
    ]
    assert artifact["ticker"] == "MC.PA"
    assert "-1 (very negative)" in content
    assert content.index("Newer article") < content.index("Older article")


def test_format_news_summary_handles_missing_sentiment():
    artifact = {
        "ticker": "MC.PA",
        "lookback_days": 30,
        "articles": [build_article("2026-10-10", "Article", None)],
    }

    summary = format_news_summary(artifact)

    assert "sentiment n/a" in summary
