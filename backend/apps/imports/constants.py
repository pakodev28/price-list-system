"""Shared import constants."""

from django.db import models


class ImportStatus(models.TextChoices):
    PENDING = "pending", "Ожидает"
    PARSING = "parsing", "Парсинг"
    DONE = "done", "Готово"
    FAILED = "failed", "Ошибка"
