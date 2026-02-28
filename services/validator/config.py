from dotenv import load_dotenv
import os

load_dotenv()


class Config:
    OUTPUT_DIR = os.getenv("VALIDATOR_OUTPUT_DIR", "data/validated_papers")
    MIN_CHAR_COUNT = 500
    MAX_CHAR_COUNT = 5_000_000
    MIN_ALPHABETIC_RATIO = 0.5
    MIN_WORD_COUNT = 100
    MAX_REPEATED_CHAR_RATIO = 0.05
