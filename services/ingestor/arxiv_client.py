import logging
from typing import Optional

import requests

from services.ingestor.config import Config

logger = logging.getLogger(__name__)


class ArxivClient:
    def __init__(self, config: type[Config]):
        self.config = config

    def search_papers(self, category: str, max_results: int) -> Optional[str]:
        """Search arXiv for papers in a category. Returns raw XML or None."""
        if max_results > self.config.MAX_PAPERS_PER_REQUEST:
            logger.warning(f"Clamping max_results to {self.config.MAX_PAPERS_PER_REQUEST}")
            max_results = self.config.MAX_PAPERS_PER_REQUEST

        params = {
            "search_query": f"cat:{category}",
            "start": 0,
            "max_results": max_results,
        }
        try:
            response = requests.get(
                self.config.ENDPOINT, params=params, timeout=self.config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"arXiv API error: {e}")
            return None
