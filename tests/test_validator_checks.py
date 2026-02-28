import pytest
from services.validator.checks import (
    check_min_length,
    check_max_length,
    check_alphabetic_ratio,
    check_word_count,
    check_repeated_characters,
    check_has_sentences,
    clean_text,
)


class TestCheckMinLength:
    def test_passes_with_enough_text(self):
        text = "a" * 600
        ok, msg = check_min_length(text)
        assert ok

    def test_fails_with_short_text(self):
        ok, msg = check_min_length("short")
        assert not ok


class TestCheckMaxLength:
    def test_passes_with_normal_text(self):
        ok, msg = check_max_length("normal text")
        assert ok

    def test_fails_with_huge_text(self):
        text = "a" * 6_000_000
        ok, msg = check_max_length(text)
        assert not ok


class TestCheckAlphabeticRatio:
    def test_passes_with_good_text(self):
        ok, msg = check_alphabetic_ratio("This is a good text with words")
        assert ok

    def test_fails_with_garbled_text(self):
        ok, msg = check_alphabetic_ratio("123 456 789 !@# $%^ &*()")
        assert not ok

    def test_fails_with_empty_text(self):
        ok, msg = check_alphabetic_ratio("")
        assert not ok


class TestCheckWordCount:
    def test_passes_with_enough_words(self):
        text = " ".join(["word"] * 150)
        ok, msg = check_word_count(text)
        assert ok

    def test_fails_with_few_words(self):
        ok, msg = check_word_count("just a few words")
        assert not ok


class TestCheckRepeatedCharacters:
    def test_passes_with_normal_text(self):
        text = "This is a normal academic paper text. " * 20
        ok, msg = check_repeated_characters(text)
        assert ok

    def test_fails_with_empty_text(self):
        ok, msg = check_repeated_characters("")
        assert not ok


class TestCheckHasSentences:
    def test_passes_with_sentences(self):
        text = (
            "This is a complete sentence. "
            "Here is another one with more words. "
            "And a third sentence for good measure."
        )
        ok, msg = check_has_sentences(text)
        assert ok

    def test_fails_with_fragments(self):
        ok, msg = check_has_sentences("word word. x. y.")
        assert not ok


class TestCleanText:
    def test_removes_extra_whitespace(self):
        result = clean_text("hello   world")
        assert "   " not in result

    def test_removes_excess_newlines(self):
        result = clean_text("hello\n\n\n\n\nworld")
        assert "\n\n\n" not in result

    def test_strips_text(self):
        result = clean_text("  hello  ")
        assert result == "hello"
