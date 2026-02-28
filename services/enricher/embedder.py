import logging
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from services.enricher.config import Config

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    """Load the embedding model once and cache it."""
    logger.info(f"Loading embedding model: {Config.EMBEDDING_MODEL}")
    return SentenceTransformer(Config.EMBEDDING_MODEL)


def generate_embedding(text: str, max_chars: int = 10_000) -> list[float]:
    """Generate a dense vector embedding from paper text."""
    model = _get_model()
    return model.encode(text[:max_chars]).tolist()
