import logging
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from services.ingestor.config import Config
from services.ingestor.downloader import Downloader
from services.ingestor.arxiv_client import ArxivClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_papers(category: str, max_results: int) -> None:
    """Ingest papers from arXiv for a given category."""
    arxiv_client = ArxivClient(Config)
    downloader = Downloader(config=Config, arxiv_client=arxiv_client)

    logger.info(f"Starting ingestion: category='{category}', max_results={max_results}")
    start = time.time()
    downloader.download_papers(category, max_results)
    logger.info(f"Finished ingestion in {time.time() - start:.2f}s")


if __name__ == "__main__":
    category = os.getenv("INGESTOR_CATEGORY", "Machine learning")
    max_results = int(os.getenv("INGESTOR_MAX_RESULTS", "10"))
    download_papers(category, max_results)
