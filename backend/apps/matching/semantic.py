"""Semantic and hybrid candidate retrieval."""

import numpy as np
from django.conf import settings

from apps.catalog.normalization import normalize_name

from .embeddings import embed_texts
from .shortlist import fuzzy_shortlist
from .types import Candidate


def _embed_query(name: str) -> np.ndarray:
    """Embed a query name with the same preprocessing as the catalog vectors."""
    return embed_texts([normalize_name(name)])[0]


def semantic_shortlist(
    name: str, candidates: list[Candidate], limit: int
) -> list[tuple[Candidate, float]]:
    """Top-``limit`` candidates by embedding cosine similarity (0..1).

    Returns ``[]`` (without loading the model) when no candidate has a vector.
    """
    with_vector = [c for c in candidates if c.vector is not None]
    if not with_vector:
        return []
    query = _embed_query(name)
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


def group_centroids(candidates: list[Candidate]) -> dict[int, np.ndarray]:
    """Unit mean vector per catalog group — depends only on the candidate set.

    Compute it once per matching run and pass it into ``retrieve``/``match`` so the
    centroids aren't rebuilt for every queried item (O(items × catalog) otherwise).
    """
    grouped: dict[int, list[np.ndarray]] = {}
    for cand in candidates:
        if cand.vector is not None and cand.group_id is not None:
            grouped.setdefault(cand.group_id, []).append(cand.vector)
    return {gid: _unit(np.mean(vecs, axis=0)) for gid, vecs in grouped.items()}


def _route_by_group(
    name: str, candidates: list[Candidate], centroids: dict[int, np.ndarray] | None = None
) -> list[Candidate]:
    """Coarse routing: keep only the catalog group(s) closest to the query.

    Compares the query embedding to per-group centroids. Ungrouped items are always
    kept; degrades to the full set when there's nothing meaningful to route.
    """
    if centroids is None:
        centroids = group_centroids(candidates)
    if len(centroids) < 2:
        return candidates
    query = _embed_query(name)
    keep = set(
        sorted(centroids, key=lambda gid: -float(centroids[gid] @ query))[
            : settings.MATCH_GROUP_TOP_N
        ]
    )
    routed = [c for c in candidates if c.group_id in keep or c.group_id is None]
    return routed or candidates


def retrieve(
    name: str,
    candidates: list[Candidate],
    limit: int,
    centroids: dict[int, np.ndarray] | None = None,
) -> list[tuple[Candidate, float]]:
    """Hybrid retrieval with *non-destructive* group routing — the production entry point.

    Routing focuses the semantic search on the catalog group(s) nearest the query
    (cutting cross-domain noise), but the global lexical top-K is always merged back
    in. A coarse, possibly-misrouted embedding can therefore never drop an obvious
    name match — e.g. "аккумулятор автомобильный" must still surface even if its
    embedding drifts toward the "автодоставка" group.

    Pass ``centroids`` (from :func:`group_centroids`) to reuse them across a batch.
    """
    keep_ids = {c.id for c in _route_by_group(name, candidates, centroids)}
    keep_ids.update(c.id for c, _score in fuzzy_shortlist(name, candidates, limit))
    pool = [c for c in candidates if c.id in keep_ids]
    return hybrid_shortlist(name, pool, limit)


def classify_group(name: str, candidates: list[Candidate]) -> int | None:
    """Suggest the catalog group whose centroid is closest to ``name``.

    A cheap, local nearest-centroid classifier (no LLM) used to pre-fill the group
    when creating a catalog product from a position. Returns ``None`` when embeddings
    are absent or no group is a confident fit — the suggestion is always
    user-overridable, so it errs toward leaving the choice open.
    """
    grouped: dict[int, list[np.ndarray]] = {}
    for cand in candidates:
        if cand.vector is not None and cand.group_id is not None:
            grouped.setdefault(cand.group_id, []).append(cand.vector)
    if not grouped:
        return None
    query = _embed_query(name)
    centroids = {gid: _unit(np.mean(vecs, axis=0)) for gid, vecs in grouped.items()}
    gid, score = max(
        ((g, float(c @ query)) for g, c in centroids.items()), key=lambda pair: pair[1]
    )
    return gid if score >= settings.MATCH_GROUP_MIN_SCORE else None
