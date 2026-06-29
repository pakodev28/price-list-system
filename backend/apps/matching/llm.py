"""LLM reranking via an OpenAI-compatible endpoint (e.g. TimeWeb cloud agent)."""

import json
import logging
import re

from django.conf import settings
from openai import OpenAI

from .prompt import SYSTEM_PROMPT, build_user_message
from .types import Candidate

logger = logging.getLogger(__name__)
_FENCE = re.compile(r"```(?:json)?|```")


def _client() -> OpenAI:
    return OpenAI(
        base_url=settings.LLM_BASE_URL,
        api_key=settings.LLM_API_KEY,
        timeout=settings.LLM_TIMEOUT,
    )


def _parse_payload(content: str) -> dict[str, object]:
    return json.loads(_FENCE.sub("", content).strip())


def rerank(
    name: str, article: str, shortlist: list[tuple[Candidate, float]]
) -> tuple[int | None, float] | None:
    """Ask the LLM to pick the best candidate.

    Returns ``(index_into_shortlist | None, confidence)`` or ``None`` if the call
    failed and the caller should fall back to fuzzy ranking.
    """
    candidates = [candidate for candidate, _score in shortlist]
    try:
        response = _client().chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_message(name, article, candidates)},
            ],
            temperature=0,
            max_tokens=settings.LLM_MAX_TOKENS,
        )
        payload = _parse_payload(response.choices[0].message.content or "")
        confidence = float(payload.get("confidence") or 0.0)
        match_id = payload.get("match_id")
        if match_id is None:
            return None, 0.0
        index = int(match_id) - 1
        if 0 <= index < len(shortlist):
            return index, confidence
        return None, 0.0
    except Exception:  # noqa: BLE001
        logger.exception("LLM rerank failed; falling back to fuzzy ranking")
        return None
