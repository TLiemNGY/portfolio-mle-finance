"""Entry point for the biweekly Cloud Run Job: refreshes portfolio and price history."""

import logging

from ingestion.batch.load_pea_csv import main as load_portfolio
from ingestion.batch.load_price_history import main as load_history

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Starting biweekly refresh job")
    load_portfolio()
    load_history()
    logger.info("Biweekly refresh job complete")


if __name__ == "__main__":
    main()
