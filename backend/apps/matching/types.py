"""Matching value objects."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Candidate:
    """A catalog product considered for matching.

    ``vector`` holds the L2-normalized name embedding (numpy array) or ``None``,
    and is excluded from equality and hashing.
    """

    id: int
    article: str
    name: str
    group_id: int | None = None
    vector: Any = field(default=None, compare=False, hash=False)


@dataclass(frozen=True)
class MatchOutcome:
    """Result of matching a single query against the catalog.

    ``source`` is one of ``article``, ``retrieval``, ``fuzzy``, ``llm`` or ``none``.
    """

    product_id: int | None
    confidence: float
    source: str
