"""Price list domain: an uploaded supplier price file and its parsed items."""

from django.db import models

from apps.catalog.models import CatalogProduct
from apps.imports.models import AbstractImportJob
from apps.suppliers.models import Supplier


class PriceList(AbstractImportJob):
    """An uploaded supplier price file; also tracks its background parse job."""

    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="price_lists")
    match_progress = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "Прайс-лист"
        verbose_name_plural = "Прайс-листы"

    def __str__(self) -> str:
        return f"{self.supplier.name}: {self.source_filename}"


class PriceListItem(models.Model):
    """A single parsed row of a price list, optionally linked to the catalog."""

    price_list = models.ForeignKey(PriceList, on_delete=models.CASCADE, related_name="items")
    row_number = models.PositiveIntegerField(default=0)
    article = models.CharField(max_length=128, blank=True)
    name = models.CharField(max_length=512)
    unit = models.CharField(max_length=32, blank=True)
    price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    catalog_product = models.ForeignKey(
        CatalogProduct,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="price_items",
    )

    class Meta:
        ordering = ["row_number"]
        verbose_name = "Позиция прайс-листа"
        verbose_name_plural = "Позиции прайс-листа"

    def __str__(self) -> str:
        return self.name
