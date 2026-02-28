from dotenv import load_dotenv
import os

load_dotenv()


class Config:
    API_URL = os.getenv("API_URL", "http://localhost:8000")
    PAGE_TITLE = "Paper Analyzer"
    PAGE_ICON = "📄"
