"""Hybrid retrieval (semantic + lexical) — vectors mocked, model never loaded."""

import numpy as np

from apps.matching import semantic
from apps.matching.types import Candidate


def _candidate(cid: int, name: str, vector: list[float]) -> Candidate:
    return Candidate(id=cid, article="", name=name, vector=np.array(vector, dtype=np.float32))


def test_semantic_shortlist_ranks_by_cosine(monkeypatch) -> None:
    candidates = [
        _candidate(1, "Морской фрахт 40HC", [1.0, 0.0]),
        _candidate(2, "Авиаперевозка", [0.0, 1.0]),
    ]
    monkeypatch.setattr(
        semantic, "embed_texts", lambda _texts: np.array([[1.0, 0.0]], dtype=np.float32)
    )

    ranked = semantic.semantic_shortlist("фрахт", candidates, 2)

    assert ranked[0][0].id == 1
    assert ranked[0][1] > ranked[1][1]


def test_semantic_shortlist_empty_without_vectors() -> None:
    """Returns [] without ever loading the embedding model when no vectors exist."""
    assert semantic.semantic_shortlist("q", [Candidate(id=1, article="", name="x")], 5) == []


def test_hybrid_surfaces_strong_semantic_match(monkeypatch) -> None:
    candidates = [
        _candidate(1, "Совсем другое", [0.0, 1.0]),
        _candidate(2, "Морской фрахт Шанхай Владивосток 40HC", [1.0, 0.0]),
    ]
    monkeypatch.setattr(
        semantic, "embed_texts", lambda _texts: np.array([[1.0, 0.0]], dtype=np.float32)
    )

    ranked = semantic.hybrid_shortlist("фрахт 40HC", candidates, 5)

    assert ranked[0][0].id == 2


def test_route_by_group_narrows_to_closest_group(monkeypatch, settings) -> None:
    settings.MATCH_GROUP_TOP_N = 1
    candidates = [
        Candidate(
            id=1,
            article="",
            name="фрахт A",
            group_id=10,
            vector=np.array([1.0, 0.0], dtype=np.float32),
        ),
        Candidate(
            id=2,
            article="",
            name="фрахт B",
            group_id=10,
            vector=np.array([0.9, 0.1], dtype=np.float32),
        ),
        Candidate(
            id=3,
            article="",
            name="электроника",
            group_id=20,
            vector=np.array([0.0, 1.0], dtype=np.float32),
        ),
        Candidate(
            id=4,
            article="",
            name="без группы",
            group_id=None,
            vector=np.array([0.5, 0.5], dtype=np.float32),
        ),
    ]
    monkeypatch.setattr(
        semantic, "embed_texts", lambda _t: np.array([[1.0, 0.0]], dtype=np.float32)
    )

    routed = {c.id for c in semantic._route_by_group("фрахт", candidates)}

    assert 3 not in routed
    assert {1, 2, 4} <= routed


def _grouped(cid: int, group_id: int, vector: list[float]) -> Candidate:
    return Candidate(
        id=cid, article="", name="x", group_id=group_id, vector=np.array(vector, dtype=np.float32)
    )


def test_retrieve_keeps_lexical_match_despite_misrouting(monkeypatch, settings) -> None:
    """A near-exact lexical match survives even when routing sends it to a far group.

    The query embeds onto group 10's centroid, so routing alone would drop the
    matching candidate (id 3) sitting in group 20.
    """
    settings.MATCH_GROUP_TOP_N = 1
    candidates = [
        _grouped(1, 10, [1.0, 0.0]),
        _grouped(2, 10, [1.0, 0.0]),
        Candidate(
            id=3,
            article="",
            name="аккумулятор автомобильный",
            group_id=20,
            vector=np.array([0.0, 1.0], dtype=np.float32),
        ),
    ]
    monkeypatch.setattr(
        semantic, "embed_texts", lambda _t: np.array([[1.0, 0.0]], dtype=np.float32)
    )

    ranked = semantic.retrieve("аккумулятор автомобильный", candidates, 5)

    assert 3 in {c.id for c, _score in ranked}


def test_precomputed_centroids_preserve_routing(monkeypatch, settings) -> None:
    settings.MATCH_GROUP_TOP_N = 1
    candidates = [
        _grouped(1, 10, [1.0, 0.0]),
        _grouped(2, 20, [0.0, 1.0]),
        Candidate(id=3, article="", name="x", vector=np.array([0.5, 0.5], dtype=np.float32)),
    ]
    monkeypatch.setattr(
        semantic, "embed_texts", lambda _t: np.array([[1.0, 0.0]], dtype=np.float32)
    )

    centroids = semantic.group_centroids(candidates)
    inline = {c.id for c in semantic._route_by_group("q", candidates)}
    precomputed = {c.id for c in semantic._route_by_group("q", candidates, centroids)}

    assert inline == precomputed == {1, 3}


def test_classify_group_picks_nearest_centroid(monkeypatch, settings) -> None:
    settings.MATCH_GROUP_MIN_SCORE = 0.5
    candidates = [_grouped(1, 10, [1.0, 0.0]), _grouped(2, 20, [0.0, 1.0])]
    monkeypatch.setattr(
        semantic, "embed_texts", lambda _t: np.array([[1.0, 0.0]], dtype=np.float32)
    )

    assert semantic.classify_group("морской фрахт", candidates) == 10


def test_classify_group_none_without_vectors() -> None:
    assert semantic.classify_group("q", [Candidate(id=1, article="", name="x")]) is None


def test_classify_group_below_floor_returns_none(monkeypatch, settings) -> None:
    """A query orthogonal to the only centroid scores ~0, below the floor."""
    settings.MATCH_GROUP_MIN_SCORE = 0.9
    monkeypatch.setattr(
        semantic, "embed_texts", lambda _t: np.array([[0.0, 1.0]], dtype=np.float32)
    )

    assert semantic.classify_group("q", [_grouped(1, 10, [1.0, 0.0])]) is None
