import pytest
from services.extractor.pdf_extractor import alphabetic_ratio


class TestAlphabeticRatio:
    def test_all_alpha(self):
        assert alphabetic_ratio("abcdef") == 1.0

    def test_no_alpha(self):
        assert alphabetic_ratio("12345") == 0.0

    def test_mixed(self):
        ratio = alphabetic_ratio("abc123")
        assert ratio == pytest.approx(0.5)

    def test_empty(self):
        assert alphabetic_ratio("") == 0.0

    def test_with_spaces(self):
        ratio = alphabetic_ratio("hello world")
        assert ratio == pytest.approx(10 / 11)
