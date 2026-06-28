"""Price list serializers."""

from rest_framework import serializers

from apps.imports.validators import validate_excel_file

from .models import PriceList, PriceListItem


class PriceListItemSerializer(serializers.ModelSerializer[PriceListItem]):
    class Meta:
        model = PriceListItem
        fields = ["id", "row_number", "article", "name", "unit", "price", "catalog_product"]


class PriceListSerializer(serializers.ModelSerializer[PriceList]):
    """Read serializer exposing import state and progress."""

    items_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = PriceList
        fields = [
            "id",
            "supplier",
            "source_filename",
            "sheet",
            "header_row",
            "mapping",
            "status",
            "progress",
            "total_rows",
            "processed_rows",
            "error",
            "row_errors",
            "items_count",
            "uploaded_at",
        ]
        read_only_fields = fields


class PriceListUploadSerializer(serializers.ModelSerializer[PriceList]):
    """Write serializer for the initial multipart upload."""

    file = serializers.FileField(write_only=True, validators=[validate_excel_file])

    class Meta:
        model = PriceList
        fields = ["id", "supplier", "file", "source_filename"]
        read_only_fields = ["source_filename"]

    def create(self, validated_data: dict) -> PriceList:
        validated_data["source_filename"] = validated_data["file"].name
        return super().create(validated_data)


class ParseRequestSerializer(serializers.Serializer):
    """Mapping configuration submitted to start parsing."""

    sheet = serializers.CharField(required=False, allow_blank=True, default="")
    header_row = serializers.IntegerField(min_value=0, default=0)
    mapping = serializers.DictField(child=serializers.IntegerField(min_value=0))

    def validate_mapping(self, value: dict[str, int]) -> dict[str, int]:
        if "name" not in value:
            raise serializers.ValidationError("Укажите колонку для поля «name» (наименование).")
        return value
