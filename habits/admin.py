# habits/admin.py

from django.contrib import admin
from .models import Place, Habit


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner", "is_public", "created_at")
    list_filter = ("is_public", "created_at")
    search_fields = ("name", "owner__email")
    raw_id_fields = ("owner",)


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "action",
        "owner",
        "place",
        "time",
        "is_pleasant",
        "frequency",
        "is_public",
        "created_at",
    )
    list_filter = ("is_pleasant", "is_public", "frequency", "created_at")
    search_fields = ("action", "owner__email", "place__name")
    raw_id_fields = ("owner", "place", "linked_habit")
    readonly_fields = ("created_at", "updated_at")