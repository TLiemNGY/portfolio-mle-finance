import argparse
import logging

from google.cloud import bigquery
from langchain_core.tools import tool

from core.clients import get_client
from core.config import DATASET, PROJECT_ID

logger = logging.getLogger(__name__)


@tool
def get_news_sentiment(ticker: str) -> dict:
    """Fetches the most relevant recent news articles for a ticker, with sentiment scores.

    Args:
        ticker: The stock ticker in Euronext Paris format (e.g. "MC.PA" for LVMH),
        NOT the company name.

    Returns up to 5 articles, deduplicated and sorted by relevance (match_score),
    each with its own sentiment_score for this specific ticker.
    """
    client = get_client()
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("ticker", "STRING", ticker)]
    )

    query = f"""
            SELECT ticker, title, description, url, source, published_at, sentiment_score, match_score
            FROM (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY ticker, url ORDER BY fetched_at DESC) AS rn
                FROM `{PROJECT_ID}.{DATASET}.news_sentiment`
                WHERE ticker = @ticker
            )
            WHERE rn = 1
            ORDER BY match_score DESC
            LIMIT 5"""
    results = client.query(query, job_config=job_config).result()
    rows = [dict(row) for row in results]

    if not rows:
        return {
            "ticker": ticker,
            "method": "error",
            "error": f"No news for {ticker}",
        }

    return {"ticker": ticker, "articles": rows}


def main(ticker):
    return get_news_sentiment.func(ticker)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", type=str, required=True)
    args = parser.parse_args()

    result = main(args.ticker)
    logger.info(result)
