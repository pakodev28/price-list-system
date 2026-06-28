"""Semantic and hybrid candidate retrieval."""

import numpy as np

from .embeddings import embed_texts
from .shortlist import fuzzy_shortlist
from .types import Candidate


def semantic_shortlist(
    name: str, candidates: list[Candidate], limit: int
) -> list[tuple[Candidate, float]]:
    """Top-``limit`` candidates by embedding cosine similarity (0..1).

    Returns ``[]`` (without loading the model) when no candidate has a vector.
    """
    with_vector = [c for c in candidates if c.vector is not None]
    if not with_vector:
        return []
    query = embed_texts([name])[0]
    matrix = np.asarray([c.vector for c in with_vector], dtype=np.float32)
    scores = matrix @ query
    order = np.argsort(-scores)[:limit]
    return [(with_vector[i], float(scores[i])) for i in order]


def hybrid_shortlist(
    name: str, candidates: list[Candidate], limit: int
) -> list[tuple[Candidate, float]]:
    """Union of lexical and semantic top-K, ranked by the stronger 0..1 signal.

    Degrades to pure lexical when embeddings are absent.
    """
    best: dict[int, tuple[Candidate, float]] = {}
    for cand, score in fuzzy_shortlist(name, candidates, limit):
        best[cand.id] = (cand, score)
    for cand, score in semantic_shortlist(name, candidates, limit):
        if cand.id not in best or score > best[cand.id][1]:
            best[cand.id] = (cand, score)
    return sorted(best.values(), key=lambda pair: -pair[1])[:limit]
