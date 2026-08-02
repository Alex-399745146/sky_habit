# users/models.py

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Менеджер пользователей с аутентификацией по email."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email обязателен")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Создание обычного пользователя."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        # username делаем необязательным: по умолчанию = email
        extra_fields.setdefault("username", email)

        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """Создание суперпользователя."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Суперпользователь должен иметь is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Суперпользователь должен иметь is_superuser=True.")

        # username по умолчанию = email
        extra_fields.setdefault("username", email)

        return self._create_user(email, password, **extra_fields)


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
    REQUIRED_FIELDS: list[str] = []  # username не обязателен

    objects = UserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["-date_joined"]  # используем существующее поле из AbstractUser

    def __str__(self):
        return self.email or f"User #{self.pk}"
