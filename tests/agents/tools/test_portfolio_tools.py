from unittest.mock import patch, MagicMock

from agents.tools.portfolio_tools import get_latest_price, get_portfolio_summary

def test_get_latest_price_returns_dict_when_found():
    fake_result = MagicMock()
    fake_result.result.return_value = [{"ticker": "MC.PA", "price_eur": 193.75, "fetched_at": "2026-09-15"}]

    with patch("agents.tools.portfolio_tools.bq_client") as mock_client:
        mock_client.query.return_value = fake_result
        result = get_latest_price.func("MC.PA")

    assert result == {"ticker": "MC.PA", "price_eur": 193.75, "fetched_at": "2026-09-15"}

def test_get_latest_price_returns_none_when_not_found():
    """Mock BigQuery to return an empty list. It verifies that the function returns None."""
    fake_result = MagicMock()
    fake_result.result.return_value = []

    with patch("agents.tools.portfolio_tools.bq_client") as mock_client:
        mock_client.query.return_value = fake_result
        result = get_latest_price.func("MC.PA")
    assert result is None

def test_get_portfolio_summary():
    fake_result = MagicMock()
    fake_result.result.return_value = [{"ticker": "MC.PA", "price_eur": 193.75, "fetched_at": "2026-09-15"},{"ticker": "OR.PA", "price_eur": 300.28, "fetched_at": "2026-09-10"}]

    with patch("agents.tools.portfolio_tools.bq_client") as mock_client:
        mock_client.query.return_value = fake_result
        result = get_portfolio_summary.func()
    assert isinstance(result, list)