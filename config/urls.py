from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from config.views import HealthCheckView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", HealthCheckView.as_view(), name="health-check"),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.groups.urls")),
    path("api/v1/", include("apps.expenses.urls")),
    path("api/v1/", include("apps.settlements.urls")),
    path("api/v1/", include("apps.balances.urls")),
    path("api/v1/", include("apps.imports.urls")),
    path("api/v1/", include("apps.ai_assistant.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
