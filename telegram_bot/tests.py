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
from telegram_bot.services import (
    TelegramNotConfigured,
    build_habit_card,
    send_habit_card,
)
from telegram_bot.tasks import (
    send_daily_reminders,
    send_telegram_message,
    send_telegram_notification,
)

User = get_user_model()


@pytest.fixture(autouse=True)
def telegram_bot_settings(settings):
    settings.TELEGRAM_BOT_TOKEN = "test-token"


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
        user=user, telegram_chat_id=123456789, telegram_username="testuser", is_active=True
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
            user=user, telegram_chat_id=987654321, telegram_username="newuser", is_active=False
        )
        assert profile.telegram_chat_id == 987654321
        assert profile.telegram_username == "newuser"
        assert profile.is_active is False
        assert profile.user == user

    def test_telegram_profile_str_with_user(self, db):
        """Тест строкового представления с пользователем."""
        user = User.objects.create_user(
            username="struser",
            email="struser@example.com",
            password="testpass123",
        )
        profile = TelegramProfile.objects.create(
            user=user,
            telegram_chat_id=111222333,
            telegram_username="withuser",
        )
        assert str(profile) == "Telegram-профиль struser@example.com @withuser"

    def test_telegram_profile_str_without_user(self, db):
        """Тест строкового представления без пользователя."""
        profile = TelegramProfile.objects.create(
            telegram_chat_id=444555666,
            telegram_username="nouser",
        )
        assert str(profile) == "Telegram-профиль не привязан @nouser"

    def test_telegram_profile_str_no_username(self, db):
        """Тест строкового представления без username."""
        profile = TelegramProfile.objects.create(
            telegram_chat_id=777888999,
        )
        assert str(profile) == "Telegram-профиль не привязан"


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

    @patch("telegram_bot.services.Bot")
    def test_send_message_success(self, mock_bot_class):
        """Тест успешной отправки сообщения."""
        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()
        mock_bot_class.return_value = mock_bot

        # Задача должна выполниться без ошибок
        send_telegram_message(123456, "Тестовое сообщение")

        mock_bot.send_message.assert_awaited_once()

    @patch("telegram_bot.services.Bot")
    @patch("telegram_bot.tasks.logger")
    def test_send_message_error(self, mock_logger, mock_bot_class):
        """Тест ошибки при отправке сообщения."""
        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock(side_effect=Exception("Ошибка сети"))
        mock_bot_class.return_value = mock_bot

        # Задача должна обработать ошибку
        send_telegram_message(123456, "Тестовое сообщение")

        mock_logger.error.assert_called_once()


class TestHabitCardService:
    """Тесты карточки привычки и принудительной отправки."""

    def test_build_habit_card(self, habit):
        """Карточка содержит основные данные привычки."""
        card = build_habit_card(habit)

        assert "Мистер Test" in card
        assert "SKY HABIT // CARD" not in card
        assert habit.action in card
        assert "Дом" in card
        assert habit.time.strftime("%H:%M") in card

    def test_build_habit_card_falls_back_to_username(self, user, place):
        """Если имя не заполнено, используется username."""
        user.first_name = ""
        user.last_name = ""
        user.username = "neo"
        user.save()
        habit = Habit.objects.create(
            owner=user,
            place=place,
            time=time(9, 0),
            action="Проснуться",
            frequency=1,
            time_to_complete=30,
        )

        card = build_habit_card(habit)

        assert "Мистер neo" in card

    def test_build_habit_card_escapes_html(self, user, place):
        """Пользовательский текст экранируется для HTML parse_mode."""
        habit = Habit.objects.create(
            owner=user,
            place=place,
            time=time(9, 0),
            action="<b>опасный</b> текст",
            frequency=1,
            time_to_complete=30,
        )

        card = build_habit_card(habit)

        assert "&lt;b&gt;опасный&lt;/b&gt; текст" in card
        assert "<b>опасный</b>" not in card

    def test_send_habit_card_requires_profile(self, user, habit):
        """Без Telegram-профиля карточка не отправляется."""
        with pytest.raises(TelegramNotConfigured):
            send_habit_card(habit)

    @patch("telegram_bot.services.Bot")
    def test_send_habit_card_sends_to_chat(self, mock_bot_class, telegram_profile, habit):
        """Карточка отправляется в chat_id профиля."""
        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()
        mock_bot_class.return_value = mock_bot

        send_habit_card(habit)

        mock_bot.send_message.assert_awaited_once()
        kwargs = mock_bot.send_message.await_args.kwargs
        assert kwargs["chat_id"] == telegram_profile.telegram_chat_id
        assert kwargs["parse_mode"] == "HTML"
        assert habit.action in kwargs["text"]
