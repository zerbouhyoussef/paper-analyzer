import logging

logger = logging.getLogger(__name__)


def extract_text_ocr(file_path: str) -> tuple[str, int]:
    """Fallback OCR extraction using pytesseract + pdf2image."""
    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError:
        logger.error("OCR dependencies not installed (pytesseract, pdf2image)")
        raise

    images = convert_from_path(file_path)
    page_count = len(images)
    text = ""
    for i, image in enumerate(images):
        logger.info(f"OCR processing page {i + 1}/{page_count}")
        text += pytesseract.image_to_string(image)
    return text, page_count
