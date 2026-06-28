"""EstimateItem serializer tests — catalog name exposure and confidence flag."""

import pytest

from apps.catalog.factories import CatalogProductFactory
from apps.projects.factories import EstimateFactory
from apps.projects.models import EstimateItem
from apps.projects.serializers import EstimateItemSerializer

pytestmark = pytest.mark.django_db


def test_exposes_catalog_name_and_article_when_matched() -> None:
    product = CatalogProductFactory(article="K1", name="Кабель X")
    item = EstimateItem.objects.create(
        estimate=EstimateFactory(),
        row_number=1,
        name="каб",
        catalog_product=product,
        match_status=EstimateItem.MatchStatus.MATCHED,
        confidence=0.9,
    )

    data = EstimateItemSerializer(item).data

    assert data["catalog_name"] == "Кабель X"
    assert data["catalog_article"] == "K1"
    assert data["is_confident"] is True


def test_null_catalog_and_low_confidence() -> None:
    item = EstimateItem.objects.create(estimate=EstimateFactory(), row_number=1, name="без матча")

    data = EstimateItemSerializer(item).data

    assert data["catalog_name"] is None
    assert data["catalog_article"] is None
    assert data["is_confident"] is False
