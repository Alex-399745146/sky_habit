from django import forms

from config.ui import apply_bootstrap_classes

from .models import TelegramProfile


class TelegramProfileForm(forms.ModelForm):
    """Привязка Telegram-профиля к пользователю."""

    class Meta:
        model = TelegramProfile
        fields = ["telegram_chat_id", "telegram_username", "is_active"]
        labels = {
            "telegram_chat_id": "Telegram chat ID",
            "telegram_username": "Telegram username",
            "is_active": "Отправлять напоминания",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_classes(self)
