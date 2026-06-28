"""Root URL configuration."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from apps.catalog.views import CatalogProductViewSet, ProductGroupViewSet
from apps.pricelists.views import PriceListViewSet
from apps.projects.views import EstimateItemViewSet, EstimateViewSet, ProjectViewSet
from apps.suppliers.views import SupplierViewSet

router = DefaultRouter()
router.register("suppliers", SupplierViewSet)
router.register("product-groups", ProductGroupViewSet)
router.register("products", CatalogProductViewSet)
router.register("price-lists", PriceListViewSet)
router.register("projects", ProjectViewSet)
router.register("estimates", EstimateViewSet)
router.register("estimate-items", EstimateItemViewSet)


def health(_request: object) -> JsonResponse:
    """Liveness probe."""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/", include(router.urls)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
