"""Compute embeddings for catalog products (semantic matching)."""

from typing import Any

from django.core.management.base import BaseCommand

from apps.matching.embeddings import embed_catalog


class Command(BaseCommand):
    help = "Compute embeddings for catalog products that don't have one yet."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--rebuild",
            action="store_true",
            help="Recompute embeddings for all products (use after the model/text changes).",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        count = embed_catalog(rebuild=options["rebuild"])
        self.stdout.write(self.style.SUCCESS(f"Эмбеддинги посчитаны для {count} товаров каталога."))
