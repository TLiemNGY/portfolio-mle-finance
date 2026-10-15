from unittest.mock import MagicMock, patch

import pytest

from agents.tools.portfolio_tools import get_latest_price, get_portfolio_summary


def build_mock_client(rows: list[dict]) -> MagicMock:
    """Builds a fake BigQuery client whose query returns the given rows."""
    mock_client = MagicMock()
    mock_client.query.return_value.result.return_value = rows
    return mock_client


def test_get_latest_price_found():
    mock_client = build_mock_client(
        [{"ticker": "MC.PA", "price_eur": 379.5, "fetched_date": "2026-10-11"}]
    )

    with patch("agents.tools.portfolio_tools.get_client", return_value=mock_client):
        content, artifact = get_latest_price.func("MC.PA")

    assert artifact["price_eur"] == 379.5
    assert "379.50 EUR" in content
    assert "2026-10-11" in content


def test_get_latest_price_not_found():
    mock_client = build_mock_client([])

    with patch("agents.tools.portfolio_tools.get_client", return_value=mock_client):
        content, artifact = get_latest_price.func("BAD.PA")

    assert artifact is None
    assert "BAD.PA" in content


def test_get_portfolio_summary_computes_weights_and_sorts_by_value():
    mock_client = build_mock_client(
        [
            {
                "ticker": "OR.PA",
                "name": "L'Oreal",
                "sector": "Consumer Goods",
                "quantity": 5,
                "current_value_eur": 800.0,
            },
            {
                "ticker": "MC.PA",
                "name": "LVMH",
                "sector": "Luxury",
                "quantity": 10,
                "current_value_eur": 1200.0,
            },
        ]
    )

    with patch("agents.tools.portfolio_tools.get_client", return_value=mock_client):
        content, artifact = get_portfolio_summary.func()

    assert artifact["total_value_eur"] == pytest.approx(2000.0)
    assert [p["ticker"] for p in artifact["positions"]] == ["MC.PA", "OR.PA"]
    assert artifact["positions"][0]["weight"] == pytest.approx(0.6)
    assert "2,000.00 EUR" in content


def test_get_portfolio_summary_empty_table():
    mock_client = build_mock_client([])

    with patch("agents.tools.portfolio_tools.get_client", return_value=mock_client):
        content, artifact = get_portfolio_summary.func()

    assert artifact is None
    assert "empty" in content
