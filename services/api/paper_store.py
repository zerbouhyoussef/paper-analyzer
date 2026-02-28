import json
import logging
import os
import time
from functools import lru_cache
from typing import Optional

import numpy as np

from data_contracts.paper import EnrichedPaper, PaperSearchResult, PaperSummary
from services.api.config import Config
from services.api.metrics import PAPERS_LOADED, SEARCH_QUERIES, SEARCH_LATENCY, INDEX_SIZE

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_embedding_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(Config.EMBEDDING_MODEL)


def _get_search_client():
    if Config.USE_AZURE_SEARCH:
        from shared.search_client import SearchClient
        return SearchClient(
            endpoint=Config.AZURE_SEARCH_ENDPOINT,
            api_key=Config.AZURE_SEARCH_API_KEY,
        )
    return None


class PaperStore:
    """Paper store with Azure AI Search backend or in-memory fallback."""

    def __init__(self) -> None:
        self.papers: dict[str, EnrichedPaper] = {}
        self._embeddings: Optional[np.ndarray] = None
        self._paper_ids: list[str] = []
        self._search_client = None

    def load_papers(self) -> None:
        """Load papers from disk. If Azure AI Search is configured, use it for search."""
        self._search_client = _get_search_client()
        if self._search_client:
            logger.info("Azure AI Search enabled for queries")

        if not os.path.exists(Config.ENRICHED_DIR):
            logger.warning(f"Enriched papers directory not found: {Config.ENRICHED_DIR}")
            return

        for name in os.listdir(Config.ENRICHED_DIR):
            if not name.endswith(".json"):
                continue
            path = os.path.join(Config.ENRICHED_DIR, name)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    paper = EnrichedPaper(**json.load(f))
                self.papers[paper.paper_id] = paper
            except Exception as e:
                logger.error(f"Failed to load {name}: {e}")

        PAPERS_LOADED.set(len(self.papers))
        logger.info(f"Loaded {len(self.papers)} papers")

        if not self._search_client:
            self._build_local_index()

    def _build_local_index(self) -> None:
        """Build the in-memory cosine-similarity index (fallback when no Azure Search)."""
        items = [(pid, p) for pid, p in self.papers.items() if p.embedding]
        if not items:
            return

        self._paper_ids = [pid for pid, _ in items]
        self._embeddings = np.array([p.embedding for _, p in items], dtype=np.float32)

        norms = np.linalg.norm(self._embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self._embeddings = self._embeddings / norms

        INDEX_SIZE.set(self._embeddings.shape[1])
        logger.info(f"Local index: {len(self._paper_ids)} papers, {self._embeddings.shape[1]} dims")

    def get_paper(self, paper_id: str) -> Optional[EnrichedPaper]:
        return self.papers.get(paper_id)

    def list_papers(self) -> list[EnrichedPaper]:
        return list(self.papers.values())

    def search(self, query: str, top_k: int = 5) -> list[PaperSearchResult]:
        """Search papers using Azure AI Search (hybrid) or local in-memory fallback."""
        SEARCH_QUERIES.inc()
        start = time.perf_counter()

        if self._search_client:
            results = self._search_azure(query, top_k)
        else:
            results = self._search_local(query, top_k)

        SEARCH_LATENCY.observe(time.perf_counter() - start)
        return results

    def _search_azure(self, query: str, top_k: int) -> list[PaperSearchResult]:
        """Hybrid search via Azure AI Search (text + vector)."""
        model = _load_embedding_model()
        embedding = model.encode(query).tolist()

        hits = self._search_client.search_hybrid(query, embedding, top_k=top_k)

        results = []
        for hit in hits:
            summary = None
            if hit.get("research_question"):
                summary = PaperSummary(
                    research_question=hit.get("research_question", ""),
                    methodology=hit.get("methodology", ""),
                    key_findings=hit.get("key_findings", []),
                    contributions=hit.get("contributions", ""),
                    limitations=hit.get("limitations", ""),
                )
            results.append(PaperSearchResult(
                paper_id=hit["paper_id"],
                title=hit.get("title", ""),
                authors=hit.get("authors", []),
                abstract=hit.get("abstract"),
                summary=summary,
                topics=hit.get("topics", []),
                score=hit.get("score", 0.0),
            ))
        return results

    def _search_local(self, query: str, top_k: int) -> list[PaperSearchResult]:
        """In-memory cosine similarity search (fallback)."""
        if self._embeddings is None or not self._paper_ids:
            return []

        model = _load_embedding_model()
        q_vec = model.encode(query).astype(np.float32)
        q_vec = q_vec / (np.linalg.norm(q_vec) + 1e-8)

        scores = self._embeddings @ q_vec
        top_idx = np.argsort(scores)[::-1][:top_k]

        return [
            PaperSearchResult(
                paper_id=(p := self.papers[self._paper_ids[i]]).paper_id,
                title=p.title,
                authors=p.authors,
                abstract=p.abstract,
                summary=p.summary,
                topics=p.topics,
                score=float(scores[i]),
            )
            for i in top_idx
        ]
