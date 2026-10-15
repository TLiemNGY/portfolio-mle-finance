"""BigQuery-backed tools for querying portfolio holdings and market prices."""

from google.cloud import bigquery
from langchain_core.tools import tool

from core.clients import get_client
from core.config import DATASET, PROJECT_ID


def format_portfolio_summary(artifact: dict) -> str:
    """Builds the short text summary of the portfolio, read by the LLM."""
    header = (
        f"{len(artifact['positions'])} positions, total value "
        f"{artifact['total_value_eur']:,.2f} EUR, largest first."
    )
    lines = [header]
    for position in artifact["positions"]:
        lines.append(
            f"- {position['ticker']} · {position['name']} · {position['sector']} · "
            f"{position['quantity']} shares · {position['current_value_eur']:,.2f} EUR "
            f"({position['weight']:.1%} of the portfolio)"
        )
    return "\n".join(lines)


@tool(response_format="content_and_artifact")
def get_portfolio_summary() -> tuple[str, dict | None]:
    """Returns the positions of the user's PEA portfolio.

    Use this tool when the user asks about their holdings, the value or the
    allocation of their portfolio, or to find the ticker of a company they own.

    Returns:
        A text summary with the total value and, for each position (largest
        first): ticker, company name, sector, quantity, current value in EUR
        and weight in the portfolio. Summarize it; the full table is displayed
        to the user separately.
        If the portfolio table is empty, the summary says so.
    """
    client = get_client()
    query = f"SELECT ticker, name, sector, quantity, current_value_eur FROM `{PROJECT_ID}.{DATASET}.portfolio`"
    positions = [dict(row) for row in client.query(query).result()]

    if not positions:
        return "The portfolio table is empty.", None

    total_value_eur = sum(position["current_value_eur"] for position in positions)
    for position in positions:
        position["weight"] = position["current_value_eur"] / total_value_eur
    positions = sorted(
        positions, key=lambda position: position["current_value_eur"], reverse=True
    )

    artifact = {"total_value_eur": total_value_eur, "positions": positions}
    return format_portfolio_summary(artifact), artifact


@tool(response_format="content_and_artifact")
def get_latest_price(ticker: str) -> tuple[str, dict | None]:
    """Returns the last recorded market price of a stock.

    Use this tool when the user asks for the current price of a stock.

    Args:
        ticker: The stock ticker in Euronext Paris format (e.g. "MC.PA" for LVMH),
            NOT the company name.

    Returns:
        A text summary with the last recorded price in EUR and the date it was
        fetched. Prices are refreshed once a week, so always mention the date.
        If no price is recorded for the ticker, the summary says so.
    """
    client = get_client()
    query = f"""
        SELECT ticker, price_eur, FORMAT_TIMESTAMP('%Y-%m-%d', fetched_at) AS fetched_date
        FROM `{PROJECT_ID}.{DATASET}.market_prices`
        WHERE ticker = @ticker
        ORDER BY fetched_at DESC
        LIMIT 1
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("ticker", "STRING", ticker)]
    )
    rows = [dict(row) for row in client.query(query, job_config=job_config).result()]

    if not rows:
        return f"No recorded price for '{ticker}'.", None

    artifact = rows[0]
    content = (
        f"{artifact['ticker']}: last recorded price {artifact['price_eur']:.2f} EUR, "
        f"fetched on {artifact['fetched_date']} (prices are refreshed weekly)."
    )
    return content, artifact
