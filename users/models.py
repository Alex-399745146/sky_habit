# users/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Кастомная модель пользователя:
    - аутентификация по email;
    - username остаётся, но не используется для входа;
    - is_verified — подтверждение email.
    """

    email = models.EmailField(
        unique=True,
        verbose_name="Email",
        help_text="Уникальный email для входа и уведомлений.",
    )

    is_verified = models.BooleanField(
        default=False,
        verbose_name="Email подтверждён",
        help_text="Флаг подтверждения email (верификация).",
    )

    # username остаётся, но не используется как логин:
    # - unique=False (по умолчанию в AbstractUser он unique=True, переопределим)
    # - blank=True, чтобы можно было не заполнять
    username = models.CharField(
        max_length=150,
        unique=False,
        blank=True,
        null=True,
        verbose_name="Username",
        help_text="Необязательное поле, не используется для входа.",
    )

    # Переопределяем группы и права, чтобы не было конфликта related_name
    # с auth.User (стандартной моделью).
    groups = models.ManyToManyField(
        "auth.Group",
        verbose_name="groups",
        blank=True,
        help_text="Группы, к которым принадлежит пользователь.",
        related_name="users_user_groups",
        related_query_name="users_user",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        verbose_name="user permissions",
        blank=True,
        help_text="Специфические права пользователя.",
        related_name="users_user_permissions",
        related_query_name="users_user",
    )

    # Переопределяем поле для аутентификации и обязательные поля.
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # username не обязателен

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["-date_joined"]  # используем существующее поле из AbstractUser

    def __str__(self):
        return self.email or f"User #{self.pk}"