from django.contrib import admin

from .models import Estimate, EstimateItem, Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
    search_fields = ["name"]


class EstimateItemInline(admin.TabularInline):
    model = EstimateItem
    extra = 0
    fields = ["row_number", "name", "article", "catalog_product", "match_status", "confidence"]
    readonly_fields = ["row_number"]


@admin.register(Estimate)
class EstimateAdmin(admin.ModelAdmin):
    list_display = ["project", "source_filename", "status", "progress", "match_progress"]
    list_filter = ["status", "project"]
    inlines = [EstimateItemInline]


@admin.register(EstimateItem)
class EstimateItemAdmin(admin.ModelAdmin):
    list_display = ["name", "estimate", "match_status", "match_source", "confidence"]
    list_filter = ["match_status", "match_source"]
    search_fields = ["name", "article"]
