import pytest
from data_contracts.paper import (
    PaperMetadata,
    ExtractedPaper,
    ValidatedPaper,
    EnrichedPaper,
    PaperSummary,
    PaperSearchResult,
    ValidationResult,
    ProcessingStatus,
)


class TestPaperMetadata:
    def test_create_minimal(self):
        meta = PaperMetadata(
            paper_id="2301.00001",
            title="Test Paper",
            pdf_url="https://arxiv.org/pdf/2301.00001",
        )
        assert meta.paper_id == "2301.00001"
        assert meta.status == ProcessingStatus.INGESTED
        assert meta.authors == []
        assert meta.source == "arxiv"

    def test_create_full(self):
        meta = PaperMetadata(
            paper_id="2301.00001",
            title="Test Paper",
            authors=["Alice", "Bob"],
            abstract="A test abstract.",
            categories=["cs.AI", "cs.LG"],
            pdf_url="https://arxiv.org/pdf/2301.00001",
            published="2023-01-01T00:00:00Z",
        )
        assert len(meta.authors) == 2
        assert meta.abstract == "A test abstract."


class TestExtractedPaper:
    def test_create(self):
        paper = ExtractedPaper(
            paper_id="test",
            title="Test",
            raw_text="Some extracted text " * 100,
            extraction_method="pymupdf",
            page_count=5,
            char_count=2000,
            alphabetic_ratio=0.85,
        )
        assert paper.status == ProcessingStatus.EXTRACTED
        assert paper.authors == []

    def test_with_metadata(self):
        paper = ExtractedPaper(
            paper_id="test",
            title="Test",
            authors=["Alice"],
            abstract="Abstract here",
            raw_text="Text",
            extraction_method="pymupdf",
            page_count=1,
            char_count=4,
            alphabetic_ratio=1.0,
        )
        assert paper.authors == ["Alice"]
        assert paper.abstract == "Abstract here"


class TestValidatedPaper:
    def test_create_valid(self):
        paper = ValidatedPaper(
            paper_id="test",
            title="Test",
            clean_text="Clean text here",
            validation=ValidationResult(
                is_valid=True,
                checks={"min_length": True, "alphabetic_ratio": True},
            ),
        )
        assert paper.status == ProcessingStatus.VALIDATED
        assert paper.validation.is_valid

    def test_create_failed(self):
        paper = ValidatedPaper(
            paper_id="test",
            title="Test",
            clean_text="x",
            validation=ValidationResult(
                is_valid=False,
                checks={"min_length": False},
                errors=["Too short"],
            ),
            status=ProcessingStatus.FAILED,
        )
        assert paper.status == ProcessingStatus.FAILED
        assert not paper.validation.is_valid


class TestEnrichedPaper:
    def test_create(self):
        paper = EnrichedPaper(
            paper_id="test",
            title="Test",
            clean_text="Clean text",
            summary=PaperSummary(
                research_question="What?",
                methodology="How?",
                key_findings=["Finding 1"],
                contributions="Novel stuff",
                limitations="Limited",
            ),
            topics=["ml", "ai"],
        )
        assert paper.status == ProcessingStatus.ENRICHED
        assert len(paper.topics) == 2
        assert paper.embedding is None


class TestPaperSearchResult:
    def test_create_minimal(self):
        result = PaperSearchResult(
            paper_id="test",
            title="Test",
            score=0.95,
        )
        assert result.authors == []
        assert result.summary is None
        assert result.score == 0.95
