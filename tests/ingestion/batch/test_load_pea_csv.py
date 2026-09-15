import pandas as pd
import pytest

from ingestion.batch.load_pea_csv import validate_portfolio


def _base_row(**overrides) -> dict:
    """Builds one valid portfolio row, with optional field overrides for edge cases."""
    row = {
        "ticker": "MC.PA",
        "name": "LVMH",
        "sector": "Luxury",
        "purchase_date": pd.Timestamp("2023-01-15"),
        "quantity": 10,
        "purchase_price_eur": 150.0,
        "current_price_eur": 180.0,
        "invested_value_eur": 1500.0,
        "current_value_eur": 1800.0,
        "unrealized_pnl_eur": 300.0,
        "unrealized_pnl_pct": 20.0,
        "currency": "EUR",
        "account_type": "PEA",
    }
    row.update(overrides)
    return row


def test_valid_portfolio_passes():
    df = pd.DataFrame([_base_row()])
    validate_portfolio(df)  # should not raise


def test_missing_column_raises():
    df = pd.DataFrame([_base_row()]).drop(columns=["sector"])
    with pytest.raises(ValueError, match="Missing columns"):
        validate_portfolio(df)


def test_null_quantity_raises():
    df = pd.DataFrame([_base_row(quantity=None)])
    with pytest.raises(ValueError, match="missing quantity"):
        validate_portfolio(df)


def test_negative_quantity_raises():
    df = pd.DataFrame([_base_row(quantity=-5)])
    with pytest.raises(ValueError, match="Negative or zero quantity"):
        validate_portfolio(df)


def test_zero_purchase_price_raises():
    df = pd.DataFrame([_base_row(purchase_price_eur=0)])
    with pytest.raises(ValueError, match="Negative or zero purchase price"):
        validate_portfolio(df)


def test_pnl_below_minus_100_percent_raises():
    df = pd.DataFrame([_base_row(unrealized_pnl_pct=-150.0)])
    with pytest.raises(ValueError, match="below -100%"):
        validate_portfolio(df)


def test_future_purchase_date_raises():
    df = pd.DataFrame([_base_row(purchase_date=pd.Timestamp("2099-01-01"))])
    with pytest.raises(ValueError, match="future"):
        validate_portfolio(df)
