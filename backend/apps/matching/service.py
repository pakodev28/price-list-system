"""Matching orchestration: article → fuzzy shortlist → optional LLM rerank."""

from django.conf import settings

from . import llm, shortlist
from .semantic import hybrid_shortlist
from .types import Candidate, MatchOutcome


class MatchingService:
    """Match query items against catalog candidates.

    Pipeline: exact normalized article (confidence 1.0) → fuzzy shortlist →
    optional LLM rerank, with a deterministic fuzzy fallback if the LLM is
    disabled or unreachable.
    """

    def __init__(
        self,
        *,
        threshold: float | None = None,
        shortlist_size: int | None = None,
        use_llm: bool | None = None,
    ) -> None:
        self.threshold = settings.MATCH_THRESHOLD if threshold is None else threshold
        self.shortlist_size = (
            settings.MATCH_SHORTLIST_SIZE if shortlist_size is None else shortlist_size
        )
        configured = (
            settings.MATCHER_STRATEGY == "hybrid"
            and settings.LLM_ENABLED
            and bool(settings.LLM_BASE_URL and settings.LLM_API_KEY)
        )
        self.use_llm = configured if use_llm is None else use_llm

    def match(self, name: str, article: str, candidates: list[Candidate]) -> MatchOutcome:
        exact = shortlist.find_exact_article(article, candidates)
        if exact is not None:
            return MatchOutcome(product_id=exact.id, confidence=1.0, source="article")

        ranked = hybrid_shortlist(name, candidates, self.shortlist_size)
        if not ranked:
            return MatchOutcome(product_id=None, confidence=0.0, source="none")

        if self.use_llm:
            result = llm.rerank(name, article, ranked)
            if result is not None:
                index, confidence = result
                if index is None:
                    return MatchOutcome(product_id=None, confidence=confidence, source="llm")
                return MatchOutcome(
                    product_id=ranked[index][0].id, confidence=confidence, source="llm"
                )

        best, score = ranked[0]
        return MatchOutcome(product_id=best.id, confidence=score, source="fuzzy")
