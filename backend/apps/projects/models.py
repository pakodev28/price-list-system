"""Projects, estimates and their matched line items."""

from django.db import models

from apps.catalog.models import CatalogProduct
from apps.imports.models import AbstractImportJob


class Project(models.Model):
    """A project that groups one or more estimates."""

    name = models.CharField("Название", max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"

    def __str__(self) -> str:
        return self.name


class Estimate(AbstractImportJob):
    """An uploaded estimate file; tracks both parse and auto-match progress."""

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="estimates")
    match_progress = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "Смета"
        verbose_name_plural = "Сметы"

    def __str__(self) -> str:
        return f"{self.project.name}: {self.source_filename}"


class EstimateItem(models.Model):
    """A parsed estimate row matched against the catalog."""

    class MatchStatus(models.TextChoices):
        UNMATCHED = "unmatched", "Не сопоставлена"
        MATCHED = "matched", "Сопоставлена"
        NO_MATCH = "no_match", "Без соответствия"

    class MatchSource(models.TextChoices):
        AUTO = "auto", "Автоматически"
        MANUAL = "manual", "Вручную"

    estimate = models.ForeignKey(Estimate, on_delete=models.CASCADE, related_name="items")
    row_number = models.PositiveIntegerField(default=0)
    name = models.CharField(max_length=512)
    article = models.CharField(max_length=128, blank=True)
    unit = models.CharField(max_length=32, blank=True)
    quantity = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    material_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    installation_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

    catalog_product = models.ForeignKey(
        CatalogProduct,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="estimate_items",
    )
    match_status = models.CharField(
        max_length=16, choices=MatchStatus.choices, default=MatchStatus.UNMATCHED
    )
    match_source = models.CharField(max_length=8, choices=MatchSource.choices, blank=True)
    confidence = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["row_number"]
        verbose_name = "Позиция сметы"
        verbose_name_plural = "Позиции сметы"

    def __str__(self) -> str:
        return self.name
