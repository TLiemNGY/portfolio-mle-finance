"""Entry point for the weekly Cloud Run Job: refreshes market prices and news sentiment."""

import logging

from ingestion.streaming.fetch_market_prices import main as fetch_prices
from ingestion.streaming.fetch_news_sentiment import main as fetch_news

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Starting weekly refresh job")
    fetch_prices()
    fetch_news()
    logger.info("Weekly refresh job complete")


if __name__ == "__main__":
    main()
