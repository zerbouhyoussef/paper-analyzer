from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProcessingStatus(str, Enum):
    INGESTED = "ingested"
    EXTRACTED = "extracted"
    VALIDATED = "validated"
    ENRICHED = "enriched"
    FAILED = "failed"


class PaperMetadata(BaseModel):
    paper_id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    abstract: Optional[str] = None
    categories: list[str] = Field(default_factory=list)
    pdf_url: str
    published: Optional[str] = None
    source: str = "arxiv"
    ingested_at: datetime = Field(default_factory=_utcnow)
    status: ProcessingStatus = ProcessingStatus.INGESTED


class ExtractedPaper(BaseModel):
    paper_id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    abstract: Optional[str] = None
    raw_text: str
    extraction_method: str
    page_count: int
    char_count: int
    alphabetic_ratio: float
    extracted_at: datetime = Field(default_factory=_utcnow)
    status: ProcessingStatus = ProcessingStatus.EXTRACTED


class ValidationResult(BaseModel):
    is_valid: bool
    checks: dict[str, bool]
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class ValidatedPaper(BaseModel):
    paper_id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    abstract: Optional[str] = None
    clean_text: str
    validation: ValidationResult
    validated_at: datetime = Field(default_factory=_utcnow)
    status: ProcessingStatus = ProcessingStatus.VALIDATED


class PaperSummary(BaseModel):
    research_question: str
    methodology: str
    key_findings: list[str]
    contributions: str
    limitations: str


class EnrichedPaper(BaseModel):
    paper_id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    abstract: Optional[str] = None
    clean_text: str
    summary: PaperSummary
    topics: list[str] = Field(default_factory=list)
    embedding: Optional[list[float]] = None
    enriched_at: datetime = Field(default_factory=_utcnow)
    status: ProcessingStatus = ProcessingStatus.ENRICHED


class PaperSearchResult(BaseModel):
    paper_id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    abstract: Optional[str] = None
    summary: Optional[PaperSummary] = None
    topics: list[str] = Field(default_factory=list)
    score: float = 0.0
