# habits/admin.py

from django import forms
from django.contrib import admin

from .models import Habit, Place


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner", "is_public", "created_at")
    list_filter = ("is_public", "created_at")
    search_fields = ("name", "owner__email")


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
    readonly_fields = ("created_at", "updated_at")

    # Выпадающий список для frequency
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["frequency"].widget = forms.Select(
            choices=[
                (1, "1 день (ежедневно)"),
                (2, "2 дня"),
                (3, "3 дня"),
                (4, "4 дня"),
                (5, "5 дней"),
                (6, "6 дней"),
                (7, "7 дней (раз в неделю)"),
                (30, "30 дней"),
            ]
        )
        return form
