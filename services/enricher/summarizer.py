import json
import logging
from typing import Optional

from openai import OpenAI

from services.enricher.config import Config
from data_contracts.paper import PaperSummary

logger = logging.getLogger(__name__)

_client: Optional[OpenAI] = None

SYSTEM_PROMPT = """You are analyzing an academic research paper. Return a JSON object with exactly these fields:
{
  "research_question": "What problem does this paper address?",
  "methodology": "How did they approach it?",
  "key_findings": ["Finding 1", "Finding 2", "Finding 3"],
  "contributions": "What's novel about this work?",
  "limitations": "What are the weaknesses or limitations?"
}
Be specific and use the paper's own terminology. Return ONLY valid JSON."""

TOPIC_PROMPT = """Extract 3-8 topic keywords/phrases from this academic paper.
Return a JSON array of strings, e.g. ["machine learning", "NLP", "transformers"].
Return ONLY a valid JSON array."""


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=Config.OPENAI_API_KEY)
    return _client


def summarize_paper(text: str) -> PaperSummary:
    """Generate a structured summary of a paper using OpenAI."""
    client = _get_client()
    truncated = text[: Config.MAX_TEXT_LENGTH]

    response = client.chat.completions.create(
        model=Config.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Summarize this paper:\n\n{truncated}"},
        ],
        temperature=Config.TEMPERATURE,
        response_format={"type": "json_object"},
    )

    data = json.loads(response.choices[0].message.content)
    return PaperSummary(
        research_question=data.get("research_question", ""),
        methodology=data.get("methodology", ""),
        key_findings=data.get("key_findings", []),
        contributions=data.get("contributions", ""),
        limitations=data.get("limitations", ""),
    )


def extract_topics(text: str) -> list[str]:
    """Extract topic keywords from paper text using OpenAI."""
    client = _get_client()
    truncated = text[: Config.MAX_TEXT_LENGTH]

    response = client.chat.completions.create(
        model=Config.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": TOPIC_PROMPT},
            {"role": "user", "content": f"Extract topics from:\n\n{truncated}"},
        ],
        temperature=Config.TEMPERATURE,
    )

    raw = response.choices[0].message.content
    try:
        topics = json.loads(raw)
        if isinstance(topics, list):
            return [str(t) for t in topics]
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse topics response: {raw[:200]}")
    return []
