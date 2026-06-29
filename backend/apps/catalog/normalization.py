"""Shared text normalization for article/name matching.

Domain abbreviations (logistics / customs) are expanded to a canonical form. Both
the catalog name and the noisy supplier/estimate name pass through here, so they
converge on the same wording — boosting lexical *and* semantic recall. The
substitutions run on lowercased text before punctuation is stripped, so dots and
slashes still disambiguate abbreviations from full words (e.g. "мор." but not
"морской").
"""

import re

_ARTICLE_STRIP = re.compile(r"[^0-9a-zа-я]+", re.IGNORECASE)
_NON_NAME = re.compile(r"[^0-9a-zа-я.]+", re.IGNORECASE)
_WS = re.compile(r"\s+")

_SYNONYMS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"мор\."), "морской"),
    (re.compile(r"\bавиа\b"), "авиаперевозка"),
    (re.compile(r"ж\s*/\s*д|\bжд\b|ж\.\s*д\."), "железнодорожная"),
    (re.compile(r"\bавто\b"), "автодоставка"),
    (re.compile(r"конт\."), "контейнер"),
    (re.compile(r"хран\."), "хранение"),
    (re.compile(r"\bспб\b"), "санкт петербург"),
]


def normalize_article(value: str | None) -> str:
    """Uppercase alphanumerics only — for exact article comparison."""
    return _ARTICLE_STRIP.sub("", value or "").upper()


def _expand_synonyms(text: str) -> str:
    for pattern, replacement in _SYNONYMS:
        text = pattern.sub(replacement, text)
    return text


def normalize_name(value: str | None) -> str:
    """Lowercased, synonym-expanded, punctuation-stripped, whitespace-collapsed.

    Used for both fuzzy comparison and as the text fed to the embedding model.
    """
    text = (value or "").lower().replace(",", ".")
    text = _expand_synonyms(text)
    text = _NON_NAME.sub(" ", text)
    return _WS.sub(" ", text).strip()
