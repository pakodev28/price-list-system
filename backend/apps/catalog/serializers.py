"""Catalog serializers."""

from rest_framework import serializers

from .models import CatalogProduct, ProductGroup


class ProductGroupSerializer(serializers.ModelSerializer[ProductGroup]):
    class Meta:
        model = ProductGroup
        fields = ["id", "name"]


class CatalogProductSerializer(serializers.ModelSerializer[CatalogProduct]):
    group_name = serializers.CharField(source="group.name", read_only=True, default=None)

    class Meta:
        model = CatalogProduct
        fields = [
            "id",
            "article",
            "name",
            "unit",
            "group",
            "group_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
