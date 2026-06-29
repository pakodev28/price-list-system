"""Abstract base shared by price lists and estimates (Excel import + job state)."""

from typing import Any

from django.db import models

from .constants import ImportStatus


def import_upload_to(instance: "AbstractImportJob", filename: str) -> str:
    """Store uploads under a per-model folder, e.g. ``imports/pricelist/<file>``."""
    return f"imports/{instance._meta.model_name}/{filename}"


class AbstractImportJob(models.Model):
    """Common fields for an uploaded Excel file and its background parse job.

    The record itself tracks the job state (status/progress), so no separate
    job table is needed.
    """

    source_filename = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to=import_upload_to, blank=True)

    sheet = models.CharField(max_length=255, blank=True)
    header_row = models.PositiveIntegerField(default=0)
    mapping = models.JSONField(default=dict, blank=True)

    status = models.CharField(
        max_length=16, choices=ImportStatus.choices, default=ImportStatus.PENDING
    )
    progress = models.PositiveSmallIntegerField(default=0)
    total_rows = models.PositiveIntegerField(default=0)
    processed_rows = models.PositiveIntegerField(default=0)
    error = models.TextField(blank=True)
    row_errors = models.JSONField(default=list, blank=True)
    task_id = models.CharField(max_length=255, blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    def reset_job(self, mapping: dict[str, Any], sheet: str, header_row: int) -> None:
        """Apply a new mapping and reset job state ahead of a (re)parse."""
        self.mapping = mapping
        self.sheet = sheet
        self.header_row = header_row
        self.status = ImportStatus.PARSING
        self.progress = 0
        self.error = ""
        self.row_errors = []
