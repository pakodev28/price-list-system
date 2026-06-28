"""Deterministic candidate selection: exact article + fuzzy name shortlist."""

from collections.abc import Iterable

from rapidfuzz import fuzz, process

from apps.catalog.models import CatalogProduct
from apps.catalog.normalization import normalize_article, normalize_name

from .types import Candidate


def to_candidates(products: Iterable[CatalogProduct]) -> list[Candidate]:
    """Materialize catalog products into lightweight candidates."""
    return [Candidate(id=p.id, article=p.article, name=p.name) for p in products]


def find_exact_article(article: str, candidates: list[Candidate]) -> Candidate | None:
    """Return the candidate whose normalized article equals the query's, if any."""
    key = normalize_article(article)
    if not key:
        return None
    for candidate in candidates:
        if normalize_article(candidate.article) == key:
            return candidate
    return None


def fuzzy_shortlist(
    name: str, candidates: list[Candidate], limit: int
) -> list[tuple[Candidate, float]]:
    """Return up to ``limit`` candidates ranked by fuzzy name similarity (0..1)."""
    query = normalize_name(name)
    if not query or not candidates:
        return []
    choices = {index: normalize_name(c.name) for index, c in enumerate(candidates)}
    ranked = process.extract(query, choices, scorer=fuzz.token_sort_ratio, limit=limit)
    return [(candidates[key], score / 100.0) for _value, score, key in ranked]
