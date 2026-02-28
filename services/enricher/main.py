import json
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from services.enricher.config import Config
from services.enricher.summarizer import summarize_paper, extract_topics
from services.enricher.embedder import generate_embedding
from data_contracts.paper import ValidatedPaper, EnrichedPaper, ProcessingStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_search_client = None


def _get_search_client():
    global _search_client
    if _search_client is None and Config.INDEX_TO_SEARCH:
        from shared.search_client import SearchClient
        _search_client = SearchClient(
            endpoint=Config.AZURE_SEARCH_ENDPOINT,
            api_key=Config.AZURE_SEARCH_API_KEY,
        )
    return _search_client


def _to_search_document(paper: EnrichedPaper) -> dict:
    """Convert an EnrichedPaper to an Azure AI Search document."""
    safe_key = paper.paper_id.replace(".", "-")
    return {
        "paper_id": safe_key,
        "title": paper.title,
        "authors": paper.authors,
        "abstract": paper.abstract or "",
        "clean_text": paper.clean_text[:32_000],
        "topics": paper.topics,
        "research_question": paper.summary.research_question,
        "methodology": paper.summary.methodology,
        "key_findings": paper.summary.key_findings,
        "contributions": paper.summary.contributions,
        "limitations": paper.summary.limitations,
        "embedding": paper.embedding,
        "enriched_at": paper.enriched_at.isoformat(),
    }


def enrich_paper(validated: ValidatedPaper) -> EnrichedPaper:
    """Enrich a validated paper with AI summary, topics, and embedding."""
    logger.info(f"Enriching: {validated.title}")

    summary = summarize_paper(validated.clean_text)
    topics = extract_topics(validated.clean_text)
    embedding = generate_embedding(validated.clean_text)

    logger.info(f"Enriched: {len(topics)} topics, {len(embedding)}-dim embedding")

    return EnrichedPaper(
        paper_id=validated.paper_id,
        title=validated.title,
        authors=validated.authors,
        abstract=validated.abstract,
        clean_text=validated.clean_text,
        summary=summary,
        topics=topics,
        embedding=embedding,
    )


def process_validated_papers(input_dir: str = "data/validated_papers") -> None:
    """Batch-enrich all validated papers, save locally and optionally index to Azure AI Search."""
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(input_dir):
        logger.error(f"Input directory not found: {input_dir}")
        return

    json_files = [f for f in os.listdir(input_dir) if f.endswith(".json")]
    logger.info(f"Found {len(json_files)} validated papers to enrich")

    search_docs = []

    for json_file in json_files:
        input_path = os.path.join(input_dir, json_file)
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            validated = ValidatedPaper(**data)

            if validated.status == ProcessingStatus.FAILED:
                logger.warning(f"Skipping failed paper: {validated.title}")
                continue

            result = enrich_paper(validated)
            output_path = os.path.join(Config.OUTPUT_DIR, json_file)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result.model_dump_json(indent=2))
            logger.info(f"Saved: {output_path}")

            search_docs.append(_to_search_document(result))
        except Exception as e:
            logger.error(f"Failed to enrich {json_file}: {e}")

    client = _get_search_client()
    if client and search_docs:
        count = client.index_papers(search_docs)
        logger.info(f"Indexed {count} papers to Azure AI Search")


if __name__ == "__main__":
    process_validated_papers()
