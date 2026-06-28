"""Price list ↔ catalog linking: manual assign, create-from-position, auto-match."""

import pytest
from rest_framework.test import APIClient

from apps.catalog.factories import CatalogProductFactory
from apps.catalog.models import CatalogProduct
from apps.pricelists.factories import PriceListFactory
from apps.pricelists.models import PriceListItem
from apps.pricelists.tasks import auto_match_price_list

pytestmark = pytest.mark.django_db


def _item(**kwargs: object) -> PriceListItem:
    return PriceListItem.objects.create(price_list=PriceListFactory(), row_number=1, **kwargs)


def test_assign_links_to_catalog_product() -> None:
    product = CatalogProductFactory(article="K1", name="Кабель")
    item = _item(name="кабель", article="")

    response = APIClient().post(
        f"/api/price-list-items/{item.id}/assign/",
        {"catalog_product": product.id},
        format="json",
    )

    assert response.status_code == 200
    item.refresh_from_db()
    assert item.catalog_product_id == product.id


def test_create_product_creates_links_and_dedupes_by_article() -> None:
    client = APIClient()
    item = _item(name="Кабель ВВГ", article="VVG-1", unit="м")

    response = client.post(f"/api/price-list-items/{item.id}/create-product/", {}, format="json")
    assert response.status_code == 200
    item.refresh_from_db()
    assert item.catalog_product is not None
    assert item.catalog_product.article == "VVG-1"
    created_id = item.catalog_product_id

    # A second position with the same article reuses the catalog product.
    other = _item(name="Кабель ВВГ (дубль)", article="VVG-1", unit="м")
    client.post(f"/api/price-list-items/{other.id}/create-product/", {}, format="json")
    other.refresh_from_db()
    assert other.catalog_product_id == created_id
    assert CatalogProduct.objects.filter(article="VVG-1").count() == 1


def test_unlink_clears_catalog() -> None:
    item = _item(name="x", article="", catalog_product=CatalogProductFactory())

    response = APIClient().post(f"/api/price-list-items/{item.id}/unlink/", {}, format="json")

    assert response.status_code == 200
    item.refresh_from_db()
    assert item.catalog_product_id is None


def test_auto_match_links_confident_only(settings: object) -> None:
    settings.MATCH_THRESHOLD = 0.5  # type: ignore[attr-defined]
    price_list = PriceListFactory()
    target = CatalogProductFactory(article="K1", name="Кабель ВВГнг 3х2.5")
    CatalogProductFactory(article="T1", name="Труба стальная 20")
    PriceListItem.objects.create(
        price_list=price_list, row_number=1, name="Кабель ВВГ нг 3x2,5 мм2", article=""
    )
    PriceListItem.objects.create(
        price_list=price_list, row_number=2, name="Нечто совсем непохожее", article=""
    )

    auto_match_price_list(price_list.id)

    price_list.refresh_from_db()
    assert price_list.match_progress == 100
    assert price_list.items.get(row_number=1).catalog_product_id == target.id
    assert price_list.items.get(row_number=2).catalog_product_id is None
