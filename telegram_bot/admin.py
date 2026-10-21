# telegram_bot/admin.py

from django.contrib import admin

from .models import TelegramProfile


@admin.register(TelegramProfile)
class TelegramProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "telegram_chat_id", "telegram_username", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("user__email", "telegram_username", "telegram_chat_id")
    raw_id_fields = ("user",)
    readonly_fields = ("created_at",)
