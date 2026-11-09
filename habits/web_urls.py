from django.urls import path

from .web_views import (
    HabitCreateView,
    HabitDeleteView,
    HabitDetailView,
    HabitListView,
    HabitUpdateView,
    PlaceCreateView,
    PlaceDeleteView,
    PlaceListView,
    PlaceUpdateView,
    PublicHabitListView,
    SendAllHabitCardsView,
    SendHabitCardView,
)

app_name = "habits_web"

urlpatterns = [
    path("public/", PublicHabitListView.as_view(), name="public-list"),
    path("habits/", HabitListView.as_view(), name="list"),
    path("habits/new/", HabitCreateView.as_view(), name="create"),
    path("habits/send-telegram/", SendAllHabitCardsView.as_view(), name="send-telegram-all"),
    path("habits/<int:pk>/send-telegram/", SendHabitCardView.as_view(), name="send-telegram"),
    path("habits/<int:pk>/", HabitDetailView.as_view(), name="detail"),
    path("habits/<int:pk>/edit/", HabitUpdateView.as_view(), name="edit"),
    path("habits/<int:pk>/delete/", HabitDeleteView.as_view(), name="delete"),
    path("places/", PlaceListView.as_view(), name="place-list"),
    path("places/new/", PlaceCreateView.as_view(), name="place-create"),
    path("places/<int:pk>/edit/", PlaceUpdateView.as_view(), name="place-edit"),
    path("places/<int:pk>/delete/", PlaceDeleteView.as_view(), name="place-delete"),
]
