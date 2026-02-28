from dotenv import load_dotenv
import os

load_dotenv()


class Config:
    OUTPUT_DIR = os.getenv("INGESTOR_OUTPUT_DIR", "data/ingested_papers")
    ENDPOINT = os.getenv("ENDPOINT", "http://export.arxiv.org/api/query")
    REQUEST_TIMEOUT = 10
    MAX_PAPERS_PER_REQUEST = 20
    MAX_FILE_SIZE_MB = 50

    AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING", "")
    AZURE_CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME", "papers")
    UPLOAD_TO_BLOB = bool(AZURE_CONNECTION_STRING)
