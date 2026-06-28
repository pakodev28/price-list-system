"""Shared text normalization for article/name matching."""

import re

_ARTICLE_STRIP = re.compile(r"[^0-9a-zа-я]+", re.IGNORECASE)
_NON_NAME = re.compile(r"[^0-9a-zа-я.]+", re.IGNORECASE)
_WS = re.compile(r"\s+")


def normalize_article(value: str | None) -> str:
    """Uppercase alphanumerics only — for exact article comparison."""
    return _ARTICLE_STRIP.sub("", value or "").upper()


def normalize_name(value: str | None) -> str:
    """Lowercased, punctuation-stripped, whitespace-collapsed — for fuzzy comparison."""
    text = (value or "").lower().replace(",", ".")
    text = _NON_NAME.sub(" ", text)
    return _WS.sub(" ", text).strip()
