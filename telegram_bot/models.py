# telegram_bot/models.py

from django.conf import settings
from django.db import models


class TelegramProfile(models.Model):
    """
    Профиль пользователя в Telegram:
    - связывает пользователя с его telegram_chat_id;
    - позволяет включать/выключать рассылку.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="telegram_profile",
        verbose_name="Пользователь",
        help_text="Пользователь, привязанный к этому Telegram-аккаунту.",
    )

    telegram_chat_id = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="Telegram chat ID",
        help_text="Уникальный идентификатор чата пользователя в Telegram.",
    )

    telegram_username = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Telegram username",
        help_text="Username пользователя в Telegram (необязательно).",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Активная рассылка",
        help_text="Если False, уведомления этому пользователю не отправляются.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
        help_text="Дата и время создания профиля Telegram.",
    )

    class Meta:
        verbose_name = "Telegram-профиль"
        verbose_name_plural = "Telegram-профили"
        ordering = ["-created_at"]

    def __str__(self):
        username_part = f" @{self.telegram_username}" if self.telegram_username else ""
        return f"Telegram-профиль {self.user.email}{username_part}"