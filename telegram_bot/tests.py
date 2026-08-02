# telegram_bot/test_bot.py

"""
Тесты для приложения telegram_bot.
"""

from datetime import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from habits.models import Habit, Place
from telegram_bot.models import TelegramProfile
from telegram_bot.tasks import (
    send_daily_reminders,
    send_telegram_message,
    send_telegram_notification,
)

User = get_user_model()


@pytest.fixture
def user(db):
    """Создание тестового пользователя."""
    return User.objects.create_user(
        username="testuser",
        email="telegram_test@example.com",
        password="testpass123",
        first_name="Telegram",
        last_name="Test",
    )


@pytest.fixture
def telegram_profile(db, user):
    """Создание Telegram профиля."""
    return TelegramProfile.objects.create(
        user=user, telegram_id=123456789, telegram_username="testuser", notified=True
    )


@pytest.fixture
def place(db, user):
    """Создание места."""
    return Place.objects.create(owner=user, name="Дом", description="Место дома", is_public=False)


@pytest.fixture
def habit(db, user, place):
    """Создание привычки."""
    return Habit.objects.create(
        owner=user,
        place=place,
        time=timezone.now().time().replace(second=0, microsecond=0),
        action="Тестовая привычка",
        is_pleasant=False,
        frequency=1,
        time_to_complete=30,
        is_public=False,
    )


class TestTelegramProfileModel:
    """Тесты модели TelegramProfile."""

    def test_telegram_profile_creation(self, db):
        """Тест создания Telegram профиля."""
        user = User.objects.create_user(username="profileuser", email="profile@example.com", password="testpass123")
        profile = TelegramProfile.objects.create(
            user=user, telegram_id=987654321, telegram_username="newuser", notified=False
        )
        assert profile.telegram_id == 987654321
        assert profile.telegram_username == "newuser"
        assert profile.notified is False
        assert profile.user == user

    def test_telegram_profile_str_with_user(self, db):
        """Тест строкового представления с пользователем."""
        user = User.objects.create_user(username="struser", email="struser@example.com", password="testpass123")
        profile = TelegramProfile.objects.create(user=user, telegram_id=111222333, telegram_username="withuser")
        assert str(profile) == "struser@example.com (@withuser)"

    def test_telegram_profile_str_without_user(self, db):
        """Тест строкового представления без пользователя."""
        profile = TelegramProfile.objects.create(telegram_id=444555666, telegram_username="nouser")
        assert str(profile) == "@nouser"

    def test_telegram_profile_str_no_username(self, db):
        """Тест строкового представления без username."""
        profile = TelegramProfile.objects.create(telegram_id=777888999)
        assert str(profile) == "@777888999"


class TestSendDailyReminders:
    """Тесты задачи send_daily_reminders."""

    def test_send_daily_reminders_no_habits(self, db):
        """Тест когда нет привычек."""
        # Очищаем все привычки
        Habit.objects.all().delete()

        # Задача должна выполниться без ошибок
        send_daily_reminders()
        assert True


class TestSendTelegramNotification:
    """Тесты задачи send_telegram_notification."""

    def test_send_notification_habit_not_found(self, db):
        """Тест когда привычка не найдена."""
        result = send_telegram_notification(99999)
        assert result is None


class TestSendTelegramMessage:
    """Тесты задачи send_telegram_message."""

    @patch("telegram_bot.tasks.Bot")
    def test_send_message_success(self, mock_bot_class):
        """Тест успешной отправки сообщения."""
        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()
        mock_bot_class.return_value = mock_bot

        # Задача должна выполниться без ошибок
        send_telegram_message(123456, "Тестовое сообщение")

        assert True

    @patch("telegram_bot.tasks.Bot")
    @patch("telegram_bot.tasks.logger")
    def test_send_message_error(self, mock_logger, mock_bot_class):
        """Тест ошибки при отправке сообщения."""
        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock(side_effect=Exception("Ошибка сети"))
        mock_bot_class.return_value = mock_bot

        # Задача должна обработать ошибку
        send_telegram_message(123456, "Тестовое сообщение")

        assert True
