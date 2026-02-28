import logging
import re

from services.validator.config import Config

logger = logging.getLogger(__name__)

CRITICAL_CHECKS = frozenset({"min_length", "alphabetic_ratio"})


def check_min_length(text: str) -> tuple[bool, str]:
    """Verify text meets minimum character count."""
    count = len(text)
    ok = count >= Config.MIN_CHAR_COUNT
    return ok, f"Char count {count} {'>=' if ok else '<'} min {Config.MIN_CHAR_COUNT}"


def check_max_length(text: str) -> tuple[bool, str]:
    """Verify text does not exceed maximum character count."""
    count = len(text)
    ok = count <= Config.MAX_CHAR_COUNT
    return ok, f"Char count {count} {'<=' if ok else '>'} max {Config.MAX_CHAR_COUNT}"


def check_alphabetic_ratio(text: str) -> tuple[bool, str]:
    """Verify sufficient proportion of alphabetic characters."""
    if not text:
        return False, "Empty text"
    ratio = sum(c.isalpha() for c in text) / len(text)
    ok = ratio >= Config.MIN_ALPHABETIC_RATIO
    return ok, f"Alpha ratio {ratio:.2f} {'>=  ' if ok else '<'} min {Config.MIN_ALPHABETIC_RATIO}"


def check_word_count(text: str) -> tuple[bool, str]:
    """Verify text has enough words to be meaningful."""
    count = len(text.split())
    ok = count >= Config.MIN_WORD_COUNT
    return ok, f"Word count {count} {'>=  ' if ok else '<'} min {Config.MIN_WORD_COUNT}"


def check_repeated_characters(text: str) -> tuple[bool, str]:
    """Detect garbled/corrupted text via excessive repeated characters."""
    if not text:
        return False, "Empty text"
    repeated = len(re.findall(r"(.)\1{4,}", text))
    ratio = repeated / len(text)
    ok = ratio <= Config.MAX_REPEATED_CHAR_RATIO
    return ok, f"Repeat ratio {ratio:.4f} {'<=' if ok else '>'} max {Config.MAX_REPEATED_CHAR_RATIO}"


def check_has_sentences(text: str) -> tuple[bool, str]:
    """Verify text contains real sentences, not just short fragments."""
    sentences = re.split(r"[.!?]+", text)
    long_count = sum(1 for s in sentences if len(s.strip().split()) >= 5)
    ok = long_count >= 3
    return ok, f"Found {long_count} sentences with 5+ words"


def clean_text(text: str) -> str:
    """Normalize whitespace and collapse excessive newlines."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


ALL_CHECKS: dict[str, callable] = {
    "min_length": check_min_length,
    "max_length": check_max_length,
    "alphabetic_ratio": check_alphabetic_ratio,
    "word_count": check_word_count,
    "repeated_characters": check_repeated_characters,
    "has_sentences": check_has_sentences,
}
