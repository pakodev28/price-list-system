"""Test factories for the catalog."""

import factory

from .models import CatalogProduct, ProductGroup


class ProductGroupFactory(factory.django.DjangoModelFactory[ProductGroup]):
    class Meta:
        model = ProductGroup

    name = factory.Sequence(lambda n: f"Группа {n}")


class CatalogProductFactory(factory.django.DjangoModelFactory[CatalogProduct]):
    class Meta:
        model = CatalogProduct

    article = factory.Sequence(lambda n: f"ART-{n:05d}")
    name = factory.Sequence(lambda n: f"Товар {n}")
    unit = "шт"
