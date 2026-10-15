"""BigQuery-backed tool returning recent news articles for a ticker, with
their sentiment scores (ingested weekly from Marketaux, see ADR-015)."""

import argparse
import logging

from google.cloud import bigquery
from langchain_core.tools import tool

from core.clients import get_client
from core.config import DATASET, PROJECT_ID

logger = logging.getLogger(__name__)

# Only articles published in this window are considered, then the most
# relevant ones are kept (see ADR-018).
NEWS_LOOKBACK_DAYS = 30
MAX_ARTICLES = 5


def format_sentiment(score: float | None) -> str:
    """Formats a sentiment score with its sign, or 'n/a' when missing."""
    return "n/a" if score is None else f"{score:+.2f}"


def format_news_summary(artifact: dict) -> str:
    """Builds the short text summary of the news articles, read by the LLM."""
    header = (
        f"{len(artifact['articles'])} news articles for {artifact['ticker']} "
        f"over the last {artifact['lookback_days']} days, most recent first. "
        "Sentiment scores come from Marketaux, range from -1 (very negative) "
        "to +1 (very positive), and are specific to this ticker."
    )
    lines = [header]
    for article in artifact["articles"]:
        lines.append(
            f"- {article['published_date']} · {article['source']} · "
            f"{article['title']} "
            f"(sentiment {format_sentiment(article['sentiment_score'])}): "
            f"{article['description'] or ''}"
        )
    return "\n".join(lines)


@tool(response_format="content_and_artifact")
def get_news_sentiment(ticker: str) -> tuple[str, dict | None]:
    """Returns the most relevant news articles of the last 30 days for a stock,
    with a sentiment score for each article.

    Use this tool when the user asks about news, recent events or the tone of
    the press on a company. Each sentiment score measures the tone of the
    article towards this specific company; it says nothing about the future
    price.

    Args:
        ticker: The stock ticker in Euronext Paris format (e.g. "MC.PA" for LVMH),
            NOT the company name.

    Returns:
        A text summary listing up to 5 articles, most recent first, each with
        its date, source, title, sentiment score and description. Sentiment
        scores range from -1 (very negative) to +1 (very positive). Summarize
        the articles in a few sentences; the full list is displayed to the user
        separately.
        If there is no article in the last 30 days, the summary says so.
    """
    client = get_client()
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("ticker", "STRING", ticker)]
    )

    # The ticker comes from the LLM, so it is passed as a query parameter.
    # NEWS_LOOKBACK_DAYS and MAX_ARTICLES are our own constants, safe to inline.
    query = f"""
            SELECT
                title,
                description,
                url,
                source,
                FORMAT_TIMESTAMP('%Y-%m-%d', published_at) AS published_date,
                sentiment_score,
                match_score
            FROM (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY ticker, url ORDER BY fetched_at DESC) AS rn
                FROM `{PROJECT_ID}.{DATASET}.news_sentiment`
                WHERE ticker = @ticker
                AND published_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {NEWS_LOOKBACK_DAYS} DAY)
            )
            WHERE rn = 1
            ORDER BY match_score DESC
            LIMIT {MAX_ARTICLES}"""
    results = client.query(query, job_config=job_config).result()
    articles = [dict(row) for row in results]

    if not articles:
        message = (
            f"No news article found for '{ticker}' in the last "
            f"{NEWS_LOOKBACK_DAYS} days."
        )
        return message, None

    # Selected by relevance, presented by date: ISO dates (YYYY-MM-DD) sort
    # correctly as plain strings.
    articles = sorted(
        articles, key=lambda article: article["published_date"], reverse=True
    )

    artifact = {
        "ticker": ticker,
        "lookback_days": NEWS_LOOKBACK_DAYS,
        "articles": articles,
    }
    return format_news_summary(artifact), artifact


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
