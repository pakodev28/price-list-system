from django.contrib import admin

from .models import PriceList, PriceListItem


class PriceListItemInline(admin.TabularInline):
    model = PriceListItem
    extra = 0
    fields = ["row_number", "article", "name", "unit", "price", "catalog_product"]
    readonly_fields = ["row_number"]


@admin.register(PriceList)
class PriceListAdmin(admin.ModelAdmin):
    list_display = ["supplier", "source_filename", "status", "progress", "uploaded_at"]
    list_filter = ["status", "supplier"]
    inlines = [PriceListItemInline]
