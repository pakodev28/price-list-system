"""Compute embeddings for catalog products (semantic matching)."""

from typing import Any

from django.core.management.base import BaseCommand

from apps.matching.embeddings import embed_catalog


class Command(BaseCommand):
    help = "Compute embeddings for catalog products that don't have one yet."

    def handle(self, *args: Any, **options: Any) -> None:
        count = embed_catalog()
        self.stdout.write(self.style.SUCCESS(f"Эмбеддинги посчитаны для {count} товаров каталога."))
