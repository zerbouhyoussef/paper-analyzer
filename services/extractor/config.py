from dotenv import load_dotenv
import os

load_dotenv()


class Config:
    OUTPUT_DIR = os.getenv("EXTRACTOR_OUTPUT_DIR", "data/extracted_papers")
    MIN_ALPHABETIC_RATIO = 0.5
    OCR_FALLBACK_THRESHOLD = 0.3
    MAX_PAGES = 200
