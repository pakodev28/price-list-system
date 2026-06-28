"""Supplier serializers."""

from rest_framework import serializers

from .models import Supplier


class SupplierSerializer(serializers.ModelSerializer[Supplier]):
    class Meta:
        model = Supplier
        fields = ["id", "name", "inn", "currency", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]
