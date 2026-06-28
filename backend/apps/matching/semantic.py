"""Semantic and hybrid candidate retrieval."""

import numpy as np
from django.conf import settings

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


def _unit(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    return vector / norm if norm else vector


def _route_by_group(name: str, candidates: list[Candidate]) -> list[Candidate]:
    """Coarse routing: keep only the catalog group(s) closest to the query.

    Compares the query embedding to per-group centroids. Ungrouped items are always
    kept; degrades to the full set when there's nothing meaningful to route.
    """
    grouped: dict[int, list[np.ndarray]] = {}
    for cand in candidates:
        if cand.vector is not None and cand.group_id is not None:
            grouped.setdefault(cand.group_id, []).append(cand.vector)
    if len(grouped) < 2:
        return candidates
    query = embed_texts([name])[0]
    centroids = {gid: _unit(np.mean(vecs, axis=0)) for gid, vecs in grouped.items()}
    keep = set(
        sorted(centroids, key=lambda gid: -float(centroids[gid] @ query))[
            : settings.MATCH_GROUP_TOP_N
        ]
    )
    routed = [c for c in candidates if c.group_id in keep or c.group_id is None]
    return routed or candidates


def retrieve(name: str, candidates: list[Candidate], limit: int) -> list[tuple[Candidate, float]]:
    """Group-routed hybrid retrieval — the production entry point."""
    return hybrid_shortlist(name, _route_by_group(name, candidates), limit)
