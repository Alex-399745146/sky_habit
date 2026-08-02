# config/urls.py

from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


urlpatterns = [
    path("admin/", admin.site.urls),

    # JWT токены.
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Пользователи.
    path("api/users/", include("users.urls")),

    # Мои приложения.
    path("api/", include("habits.urls")),

    # API
    path("api/", include("habits.urls")),
    path("api/users/", include("users.urls")),

    # Документация API
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]


# GET /api/schema/ — OpenAPI‑схема (JSON/YAML).
# GET /api/docs/ — Swagger UI.
# GET /api/redoc/ — ReDoc.