from google.cloud import bigquery

PROJECT_ID = "portfolio-mle-finance"
DATASET = "finance_data"


def get_portfolio_tickers(client: bigquery.Client) -> list[str]:
    """Returns the distinct list of tickers currently held in the portfolio."""
    query = f"SELECT DISTINCT ticker FROM `{PROJECT_ID}.{DATASET}.portfolio`"
    results = client.query(query).result()
    return [row["ticker"] for row in results]
