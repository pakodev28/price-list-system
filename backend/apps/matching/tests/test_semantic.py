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
    # No vectors -> returns [] without ever loading the embedding model.
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

    assert 3 not in routed  # far group dropped
    assert {1, 2, 4} <= routed  # near group + ungrouped kept
