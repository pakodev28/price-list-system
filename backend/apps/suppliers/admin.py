from django.contrib import admin

from .models import Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ["name", "inn", "currency", "created_at"]
    search_fields = ["name", "inn"]
    list_filter = ["currency"]
