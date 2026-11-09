# config/urls.py

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from habits.web_views import HomeView

urlpatterns = [
    # Веб-интерфейс.
    path("", HomeView.as_view(), name="home"),
    path("", include("users.web_urls")),
    path("", include("habits.web_urls")),
    # Админка.
    path("admin/", admin.site.urls),
    # JWT токены.
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Пользователи.
    path("api/users/", include("users.urls")),
    # Мои приложения.
    path("api/", include("habits.urls")),
    # Документация API
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
