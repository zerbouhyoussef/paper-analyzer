import json
import logging
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from services.extractor.config import Config
from services.extractor.pdf_extractor import extract_text_pymupdf, alphabetic_ratio
from services.extractor.ocr_extractor import extract_text_ocr
from data_contracts.paper import ExtractedPaper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _load_sidecar_metadata(pdf_path: str) -> dict:
    """Load the .meta.json sidecar written by the ingestor, if it exists."""
    meta_path = os.path.splitext(pdf_path)[0] + ".meta.json"
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def extract_paper(pdf_path: str, paper_id: str, title: str) -> ExtractedPaper:
    """Extract text from a PDF, falling back to OCR if quality is too low."""
    logger.info(f"Extracting: {title}")
    start = time.time()
    meta = _load_sidecar_metadata(pdf_path)

    text, page_count = extract_text_pymupdf(pdf_path)
    method = "pymupdf"
    ratio = alphabetic_ratio(text)

    if ratio < Config.OCR_FALLBACK_THRESHOLD:
        logger.warning(f"Low quality ({ratio:.2f}), falling back to OCR")
        try:
            text, page_count = extract_text_ocr(pdf_path)
            method = "ocr"
            ratio = alphabetic_ratio(text)
        except Exception as e:
            logger.error(f"OCR fallback failed: {e}")

    logger.info(f"Done in {time.time() - start:.2f}s ({method}, {len(text)} chars, ratio={ratio:.2f})")

    return ExtractedPaper(
        paper_id=meta.get("paper_id", paper_id),
        title=meta.get("title", title),
        authors=meta.get("authors", []),
        abstract=meta.get("abstract"),
        raw_text=text,
        extraction_method=method,
        page_count=page_count,
        char_count=len(text),
        alphabetic_ratio=ratio,
    )


def process_ingested_papers(input_dir: str = "data/ingested_papers") -> None:
    """Batch-process all PDFs in the ingested papers directory."""
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(input_dir):
        logger.error(f"Input directory not found: {input_dir}")
        return

    pdf_files = [f for f in os.listdir(input_dir) if f.endswith(".pdf")]
    logger.info(f"Found {len(pdf_files)} PDFs to extract")

    for pdf_file in pdf_files:
        pdf_path = os.path.join(input_dir, pdf_file)
        paper_id = os.path.splitext(pdf_file)[0].replace(" ", "_").lower()
        title = os.path.splitext(pdf_file)[0]

        try:
            result = extract_paper(pdf_path, paper_id, title)
            output_path = os.path.join(Config.OUTPUT_DIR, f"{paper_id}.json")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result.model_dump_json(indent=2))
            logger.info(f"Saved: {output_path}")
        except Exception as e:
            logger.error(f"Failed to extract {pdf_file}: {e}")


if __name__ == "__main__":
    process_ingested_papers()
