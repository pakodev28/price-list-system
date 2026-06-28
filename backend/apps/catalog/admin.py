from django.contrib import admin

from .models import CatalogProduct, ProductGroup


@admin.register(ProductGroup)
class ProductGroupAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(CatalogProduct)
class CatalogProductAdmin(admin.ModelAdmin):
    list_display = ["article", "name", "unit", "group"]
    search_fields = ["article", "name"]
    list_filter = ["group"]
