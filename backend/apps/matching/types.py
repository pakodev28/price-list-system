"""Matching value objects."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Candidate:
    """A catalog product considered for matching."""

    id: int
    article: str
    name: str
    # L2-normalized embedding (numpy array) or None; excluded from eq/hash.
    vector: Any = field(default=None, compare=False, hash=False)


@dataclass(frozen=True)
class MatchOutcome:
    """Result of matching a single query against the catalog."""

    product_id: int | None
    confidence: float
    source: str  # "article" | "fuzzy" | "llm" | "none"
