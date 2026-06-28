"""Supplier domain model."""

from django.core.validators import RegexValidator
from django.db import models

inn_validator = RegexValidator(
    regex=r"^\d{10}(\d{2})?$",
    message="ИНН должен содержать 10 (юр. лицо) или 12 (ИП) цифр.",
)


class Supplier(models.Model):
    """A goods supplier with its own price lists."""

    class Currency(models.TextChoices):
        RUB = "RUB", "₽ RUB"
        USD = "USD", "$ USD"
        EUR = "EUR", "€ EUR"
        CNY = "CNY", "¥ CNY"

    name = models.CharField("Название", max_length=255)
    inn = models.CharField("ИНН", max_length=12, validators=[inn_validator])
    currency = models.CharField(
        "Валюта", max_length=3, choices=Currency.choices, default=Currency.RUB
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Поставщик"
        verbose_name_plural = "Поставщики"

    def __str__(self) -> str:
        return self.name
