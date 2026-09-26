from unittest.mock import MagicMock, patch

from agents.tools.portfolio_tools import get_latest_price, get_portfolio_summary


def test_get_latest_price_returns_dict_when_found():
    fake_result = MagicMock()
    fake_result.result.return_value = [
        {"ticker": "MC.PA", "price_eur": 193.75, "fetched_at": "2026-09-15"}
    ]

    mock_client = MagicMock()
    mock_client.query.return_value = fake_result

    with patch("agents.tools.portfolio_tools.get_client", return_value=mock_client):
        result = get_latest_price.func("MC.PA")

    assert result == {
        "ticker": "MC.PA",
        "price_eur": 193.75,
        "fetched_at": "2026-09-15",
    }


def test_get_latest_price_returns_none_when_not_found():
    fake_result = MagicMock()
    fake_result.result.return_value = []

    mock_client = MagicMock()
    mock_client.query.return_value = fake_result

    with patch("agents.tools.portfolio_tools.get_client", return_value=mock_client):
        result = get_latest_price.func("MC.PA")

    assert result is None


def test_get_portfolio_summary():
    fake_result = MagicMock()
    fake_result.result.return_value = [
        {
            "ticker": "MC.PA",
            "name": "LVMH",
            "sector": "Luxury",
            "quantity": 10,
            "current_value_eur": 1500.0,
        },
        {
            "ticker": "OR.PA",
            "name": "L'Oreal",
            "sector": "Consumer Goods",
            "quantity": 5,
            "current_value_eur": 800.0,
        },
    ]

    mock_client = MagicMock()
    mock_client.query.return_value = fake_result

    with patch("agents.tools.portfolio_tools.get_client", return_value=mock_client):
        result = get_portfolio_summary.func()

    assert result == [
        {
            "ticker": "MC.PA",
            "name": "LVMH",
            "sector": "Luxury",
            "quantity": 10,
            "current_value_eur": 1500.0,
        },
        {
            "ticker": "OR.PA",
            "name": "L'Oreal",
            "sector": "Consumer Goods",
            "quantity": 5,
            "current_value_eur": 800.0,
        },
    ]
