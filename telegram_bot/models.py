# telegram_bot/models.py

from django.conf import settings
from django.db import models


class TelegramProfile(models.Model):
    """Профиль пользователя Telegram"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="telegram_profile",
        null=True,
        blank=True,
        help_text="Привязанный пользователь Sky Habit",
    )
    telegram_id = models.BigIntegerField(
        "Telegram ID",
        unique=True,
        help_text="Telegram user ID",
    )
    telegram_username = models.CharField(
        "Username",
        max_length=255,
        blank=True,
        null=True,
    )
    notified = models.BooleanField(
        "Уведомления включены",
        default=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Telegram профиль"
        verbose_name_plural = "Telegram профили"

    def __str__(self):
        username = self.telegram_username or self.telegram_id
        if self.user:
            return f"{self.user.email} (@{username})"
        return f"@{username}"
