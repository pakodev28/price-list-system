"""Matching value objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Candidate:
    """A catalog product considered for matching."""

    id: int
    article: str
    name: str


@dataclass(frozen=True)
class MatchOutcome:
    """Result of matching a single query against the catalog."""

    product_id: int | None
    confidence: float
    source: str  # "article" | "fuzzy" | "llm" | "none"
