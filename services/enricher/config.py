from dotenv import load_dotenv
import os

load_dotenv()


class Config:
    OUTPUT_DIR = os.getenv("ENRICHER_OUTPUT_DIR", "data/enriched_papers")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    MAX_TEXT_LENGTH = 100_000
    TEMPERATURE = 0.2

    AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "")
    AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY", "")
    INDEX_TO_SEARCH = bool(AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_API_KEY)
