from dotenv import load_dotenv
import os

load_dotenv()


class Config:
    HOST = os.getenv("API_HOST", "0.0.0.0")
    PORT = int(os.getenv("API_PORT", "8000"))
    DATA_DIR = os.getenv("DATA_DIR", "data")
    ENRICHED_DIR = os.path.join(DATA_DIR, "enriched_papers")
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"

    AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "")
    AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY", "")
    USE_AZURE_SEARCH = bool(AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_API_KEY)
