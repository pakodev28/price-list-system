"""Matching service tests (LLM disabled — deterministic paths)."""

import pytest

from apps.catalog.factories import CatalogProductFactory
from apps.catalog.models import CatalogProduct
from apps.matching.service import MatchingService
from apps.matching.shortlist import to_candidates

pytestmark = pytest.mark.django_db


def _candidates() -> list:
    return to_candidates(CatalogProduct.objects.all())


def test_exact_article_wins() -> None:
    target = CatalogProductFactory(article="ВВГ-3х2.5", name="Кабель ВВГ 3х2.5")
    CatalogProductFactory(article="ПВС-2х1.5", name="Провод ПВС 2х1.5")

    outcome = MatchingService(use_llm=False).match(
        name="неважно", article="ВВГ 3х2,5", candidates=_candidates()
    )

    assert outcome.source == "article"
    assert outcome.product_id == target.id
    assert outcome.confidence == 1.0


def test_fuzzy_picks_closest_name() -> None:
    target = CatalogProductFactory(article="A1", name="Кабель ВВГнг 3х2.5")
    CatalogProductFactory(article="A2", name="Труба стальная 20")

    outcome = MatchingService(use_llm=False).match(
        name="Кабель ВВГ нг 3x2,5 мм2", article="", candidates=_candidates()
    )

    assert outcome.source == "fuzzy"
    assert outcome.product_id == target.id
    assert outcome.confidence > 0.5


def test_no_candidates_yields_none() -> None:
    outcome = MatchingService(use_llm=False).match(name="Кабель", article="", candidates=[])
    assert outcome.product_id is None
    assert outcome.source == "none"
