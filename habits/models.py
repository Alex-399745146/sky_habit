# habits/models.py

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Place(models.Model):
    """
    Место выполнения привычки.
    - принадлежит пользователю (owner);
    - может быть публичным или приватным.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="places",
        verbose_name="Владелец",
        help_text="Пользователь, создавший это место.",
    )

    name = models.CharField(
        max_length=255,
        verbose_name="Название места",
        help_text="Например: 'Дом', 'Офис', 'Спортзал'.",
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Описание",
        help_text="Опциональное описание места.",
    )

    is_public = models.BooleanField(
        default=False,
        verbose_name="Публичное место",
        help_text="Если True, место видно другим пользователям.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )

    class Meta:
        verbose_name = "Место"
        verbose_name_plural = "Места"
        ordering = ["-created_at"]
        unique_together = ["owner", "name"]  # уникальность имени в рамках владельца

    def __str__(self):
        return f"{self.name} ({self.owner.email})"


class Habit(models.Model):
    """
    Привычка пользователя.
    - полезная или приятная;
    - может иметь вознаграждение или связанную привычку;
    - публичная или приватная.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="habits",
        verbose_name="Владелец",
        help_text="Пользователь, создавший привычку.",
    )

    place = models.ForeignKey(
        Place,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="habits",
        verbose_name="Место",
        help_text="Место выполнения привычки (необязательно).",
    )

    time = models.TimeField(
        verbose_name="Время выполнения",
        help_text="Время суток, когда нужно выполнить привычку.",
    )

    action = models.CharField(
        max_length=255,
        verbose_name="Действие",
        help_text="Описание действия, например: 'я буду делать зарядку'.",
    )

    is_pleasant = models.BooleanField(
        default=False,
        verbose_name="Приятная привычка",
        help_text="Если True, привычка является приятной (вознаграждением).",
    )

    linked_habit = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="linked_as_reward",
        verbose_name="Связанная привычка",
        help_text="Привычка, которая является вознаграждением (только для полезных привычек).",
    )

    reward = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Вознаграждение",
        help_text="Текстовое описание вознаграждения (не для приятных привычек).",
    )

    frequency = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(7)],
        verbose_name="Периодичность (дней)",
        help_text="Периодичность выполнения в днях (от 1 до 7).",
    )

    time_to_complete = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(120)],
        verbose_name="Время на выполнение (сек)",
        help_text="Предполагаемое время выполнения в секундах (макс. 120).",
    )

    is_public = models.BooleanField(
        default=False,
        verbose_name="Публичная привычка",
        help_text="Если True, привычка видна другим пользователям.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления",
    )

    class Meta:
        verbose_name = "Привычка"
        verbose_name_plural = "Привычки"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} ({self.owner.email})"

    def clean(self):
        """
        Валидация бизнес-правил на уровне модели:
        1. Нельзя одновременно указать reward и linked_habit.
        2. У приятной привычки не может быть reward или linked_habit.
        3. linked_habit должна указывать только на приятную привычку.
        """
        super().clean()

        # 1. Нельзя одновременно reward и linked_habit
        if self.reward and self.linked_habit:
            raise ValidationError("Нельзя одновременно указать вознаграждение и связанную привычку.")

        # 2. У приятной привычки не может быть reward или linked_habit
        if self.is_pleasant:
            if self.reward:
                raise ValidationError("У приятной привычки не может быть вознаграждения.")
            if self.linked_habit:
                raise ValidationError("У приятной привычки не может быть связанной привычки.")

        # 3. linked_habit должна указывать только на приятную привычку
        if self.linked_habit and not self.linked_habit.is_pleasant:
            raise ValidationError("Связанная привычка должна быть приятной.")
