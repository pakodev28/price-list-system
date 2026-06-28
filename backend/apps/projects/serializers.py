"""Project / estimate serializers."""

from django.conf import settings
from rest_framework import serializers

from apps.imports.validators import validate_excel_file

from .models import Estimate, EstimateItem, Project


class ProjectSerializer(serializers.ModelSerializer[Project]):
    estimates_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Project
        fields = ["id", "name", "estimates_count", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class EstimateItemSerializer(serializers.ModelSerializer[EstimateItem]):
    """Read serializer for the matching table; ``is_confident`` drives colour."""

    is_confident = serializers.SerializerMethodField()
    catalog_article = serializers.CharField(
        source="catalog_product.article", read_only=True, default=None
    )
    catalog_name = serializers.CharField(
        source="catalog_product.name", read_only=True, default=None
    )

    class Meta:
        model = EstimateItem
        fields = [
            "id",
            "row_number",
            "name",
            "article",
            "unit",
            "quantity",
            "material_price",
            "installation_price",
            "catalog_product",
            "catalog_article",
            "catalog_name",
            "match_status",
            "match_source",
            "confidence",
            "is_confident",
        ]
        read_only_fields = [
            "row_number",
            "name",
            "article",
            "unit",
            "quantity",
            "material_price",
            "installation_price",
            "catalog_product",
            "match_status",
            "match_source",
            "confidence",
        ]

    def get_is_confident(self, obj: EstimateItem) -> bool:
        return (
            obj.match_status == EstimateItem.MatchStatus.MATCHED
            and (obj.confidence or 0.0) >= settings.MATCH_THRESHOLD
        )


class EstimateSerializer(serializers.ModelSerializer[Estimate]):
    items_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Estimate
        fields = [
            "id",
            "project",
            "source_filename",
            "sheet",
            "header_row",
            "mapping",
            "status",
            "progress",
            "match_progress",
            "total_rows",
            "processed_rows",
            "error",
            "row_errors",
            "items_count",
            "uploaded_at",
        ]
        read_only_fields = fields


class EstimateUploadSerializer(serializers.ModelSerializer[Estimate]):
    file = serializers.FileField(write_only=True, validators=[validate_excel_file])

    class Meta:
        model = Estimate
        fields = ["id", "project", "file", "source_filename"]
        read_only_fields = ["source_filename"]

    def create(self, validated_data: dict) -> Estimate:
        validated_data["source_filename"] = validated_data["file"].name
        return super().create(validated_data)


class ParseEstimateRequestSerializer(serializers.Serializer):
    sheet = serializers.CharField(required=False, allow_blank=True, default="")
    header_row = serializers.IntegerField(min_value=0, default=0)
    mapping = serializers.DictField(child=serializers.IntegerField(min_value=0))

    def validate_mapping(self, value: dict[str, int]) -> dict[str, int]:
        if "name" not in value:
            raise serializers.ValidationError("Укажите колонку для поля «name» (наименование).")
        return value
