# habits/urls.py

from django.urls import path

from .views import (
    HabitDetailView,
    HabitListCreateView,
    PlaceDetailView,
    PlaceListCreateView,
    PublicHabitListView,
)

app_name = "habits"

urlpatterns = [
    # Места.
    path("places/", PlaceListCreateView.as_view(), name="place-list-create"),
    path("places/<int:pk>/", PlaceDetailView.as_view(), name="place-detail"),
    # Привычки текущего пользователя.
    path("habits/", HabitListCreateView.as_view(), name="habit-list-create"),
    path("habits/<int:pk>/", HabitDetailView.as_view(), name="habit-detail"),
    # Публичные привычки.
    path("habits/public/", PublicHabitListView.as_view(), name="habit-public-list"),
]
