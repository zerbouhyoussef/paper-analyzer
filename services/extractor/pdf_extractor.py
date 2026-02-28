import logging

import pymupdf

logger = logging.getLogger(__name__)


def extract_text_pymupdf(file_path: str) -> tuple[str, int]:
    """Extract text from a PDF using pymupdf. Returns (text, page_count)."""
    doc = pymupdf.open(file_path)
    page_count = len(doc)
    pages = [page.get_text() for page in doc]
    doc.close()
    return "".join(pages), page_count


def alphabetic_ratio(text: str) -> float:
    """Fraction of characters that are alphabetic. Returns 0.0 for empty text."""
    if not text:
        return 0.0
    return sum(c.isalpha() for c in text) / len(text)
