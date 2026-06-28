"""Catalog domain: product groups and the central product catalog."""

from django.db import models


class ProductGroup(models.Model):
    """A product category used to organize the catalog."""

    name = models.CharField("Название", max_length=255, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Группа товаров"
        verbose_name_plural = "Группы товаров"

    def __str__(self) -> str:
        return self.name


class CatalogProduct(models.Model):
    """A catalog product — the hub that supplier and estimate items link to."""

    article = models.CharField("Артикул", max_length=128, unique=True)
    name = models.CharField("Наименование", max_length=512)
    unit = models.CharField("Ед. изм.", max_length=32, blank=True)
    group = models.ForeignKey(
        ProductGroup,
        verbose_name="Группа",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products",
    )
    # L2-normalized sentence embedding (float32 bytes) for semantic matching.
    embedding = models.BinaryField(null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Товар каталога"
        verbose_name_plural = "Каталог товаров"

    def __str__(self) -> str:
        return f"{self.article} — {self.name}"
