"""Matching orchestration: article → group-routed hybrid retrieval → gated LLM rerank."""

import numpy as np
from django.conf import settings

from . import llm, shortlist
from .semantic import retrieve
from .types import Candidate, MatchOutcome


class MatchingService:
    """Match query items against catalog candidates.

    Pipeline: exact article (1.0) → group-routed hybrid retrieval (lexical + semantic)
    → confidence gate. Strong matches are accepted without the LLM, weak ones are
    rejected as "no match", and only the ambiguous middle is escalated to the LLM
    reranker — so the slow/paid model is used for a small minority of items.
    """

    def __init__(
        self,
        *,
        threshold: float | None = None,
        shortlist_size: int | None = None,
        accept_threshold: float | None = None,
        floor: float | None = None,
        use_llm: bool | None = None,
    ) -> None:
        self.threshold = settings.MATCH_THRESHOLD if threshold is None else threshold
        self.shortlist_size = (
            settings.MATCH_SHORTLIST_SIZE if shortlist_size is None else shortlist_size
        )
        self.accept_threshold = (
            settings.MATCH_ACCEPT_THRESHOLD if accept_threshold is None else accept_threshold
        )
        self.floor = settings.MATCH_FLOOR if floor is None else floor
        configured = (
            settings.MATCHER_STRATEGY == "hybrid"
            and settings.LLM_ENABLED
            and bool(settings.LLM_BASE_URL and settings.LLM_API_KEY)
        )
        self.use_llm = configured if use_llm is None else use_llm

    def match(
        self,
        name: str,
        article: str,
        candidates: list[Candidate],
        centroids: dict[int, np.ndarray] | None = None,
    ) -> MatchOutcome:
        exact = shortlist.find_exact_article(article, candidates)
        if exact is not None:
            return MatchOutcome(product_id=exact.id, confidence=1.0, source="article")

        ranked = retrieve(name, candidates, self.shortlist_size, centroids)
        if not ranked:
            return MatchOutcome(product_id=None, confidence=0.0, source="none")

        best, score = ranked[0]
        if score >= self.accept_threshold:  # confident → accept without the LLM
            return MatchOutcome(product_id=best.id, confidence=score, source="retrieval")
        if score < self.floor:  # too weak → don't force a match
            return MatchOutcome(product_id=None, confidence=score, source="none")

        if self.use_llm:  # ambiguous middle → let the LLM decide
            result = llm.rerank(name, article, ranked)
            if result is not None:
                index, confidence = result
                if index is None:
                    return MatchOutcome(product_id=None, confidence=confidence, source="llm")
                return MatchOutcome(
                    product_id=ranked[index][0].id, confidence=confidence, source="llm"
                )

        return MatchOutcome(product_id=best.id, confidence=score, source="fuzzy")
