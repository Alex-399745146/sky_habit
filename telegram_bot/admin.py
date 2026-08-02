# telegram_bot/admin.py

from django.contrib import admin

from .models import TelegramProfile


@admin.register(TelegramProfile)
class TelegramProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "telegram_username",
        "telegram_id",
        "notified",
        "created_at",
    )
    list_filter = ("notified", "created_at")
    search_fields = ("user__email", "telegram_username", "telegram_id")
    readonly_fields = ("created_at", "updated_at")
