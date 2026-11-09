import datetime
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from habits.models import Habit, Place
from telegram_bot.models import TelegramProfile
from telegram_bot.services import TelegramNotConfigured
from users.services import EmailVerificationService

User = get_user_model()

pytestmark = pytest.mark.django_db

PASSWORD = "MatrixPass123!"


@pytest.fixture
def user():
    return User.objects.create_user(email="web@example.com", password=PASSWORD)


@pytest.fixture
def other_user():
    return User.objects.create_user(email="other@example.com", password=PASSWORD)


@pytest.fixture
def auth_client(client, user):
    client.force_login(user)
    return client


def make_habit(owner, action="Зарядка", is_public=True, **kwargs):
    defaults = {
        "owner": owner,
        "action": action,
        "time": datetime.time(7, 0),
        "frequency": 1,
        "time_to_complete": 30,
        "is_public": is_public,
    }
    defaults.update(kwargs)
    return Habit.objects.create(**defaults)


def test_home_shows_public_habits(client, user):
    make_habit(user, action="Публичная зарядка", is_public=True)
    make_habit(user, action="Секретная привычка", is_public=False)

    response = client.get(reverse("home"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Публичная зарядка" in content
    assert "Секретная привычка" not in content
    assert 'id="matrix-rain"' in content


def test_public_list_hides_private_habits(client, user):
    make_habit(user, action="Публичная привычка", is_public=True)
    make_habit(user, action="Приватная привычка", is_public=False)

    response = client.get(reverse("habits_web:public-list"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Публичная привычка" in content
    assert "Приватная привычка" not in content


def test_my_habits_requires_login(client):
    response = client.get(reverse("habits_web:list"))

    assert response.status_code == 302
    assert reverse("users_web:login") in response.url


def test_register_creates_user_and_sends_email(client, mailoutbox):
    response = client.post(
        reverse("users_web:register"),
        {
            "email": "new@example.com",
            "first_name": "Иван",
            "last_name": "Тестов",
            "password1": PASSWORD,
            "password2": PASSWORD,
        },
    )

    created = User.objects.get(email="new@example.com")
    assert response.status_code == 302
    assert created.username == "new@example.com"
    assert created.is_verified is False
    assert len(mailoutbox) == 1
    assert "new@example.com" in mailoutbox[0].to
    assert "/verify/" in mailoutbox[0].body
    assert client.get(reverse("users_web:profile")).status_code == 200


def test_verify_email_link(client, user):
    token = EmailVerificationService.issue_verification_token(user)

    response = client.get(reverse("users_web:verify", args=[token.token]))

    user.refresh_from_db()
    assert response.status_code == 302
    assert user.is_verified is True


def test_telegram_guide_page(client):
    response = client.get(reverse("users_web:telegram-guide"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "chat ID" in content
    assert "username" in content.lower()
    assert "Открыть @" in content


def test_profile_links_to_telegram_guide(auth_client):
    response = auth_client.get(reverse("users_web:profile"))

    assert response.status_code == 200
    assert reverse("users_web:telegram-guide") in response.content.decode()


def test_resend_verification_email(auth_client, user, mailoutbox):
    response = auth_client.post(reverse("users_web:resend-verification"))

    assert response.status_code == 302
    assert len(mailoutbox) == 1
    assert "/verify/" in mailoutbox[0].body


def test_invalid_verify_email_link(client):
    response = client.get(reverse("users_web:verify", args=["bad-token"]), follow=True)

    assert response.status_code == 200
    assert "недействительна или истекла" in response.content.decode()


def test_login_by_email(client, user):
    response = client.post(
        reverse("users_web:login"),
        {"username": user.email, "password": PASSWORD},
    )

    assert response.status_code == 302
    assert client.get(reverse("users_web:profile")).status_code == 200


def test_create_habit_sets_owner(auth_client, user):
    response = auth_client.post(
        reverse("habits_web:create"),
        {
            "action": "Читать 10 страниц",
            "time": "21:30",
            "frequency": 1,
            "time_to_complete": 45,
        },
    )

    habit = Habit.objects.get(action="Читать 10 страниц")
    assert response.status_code == 302
    assert habit.owner == user


def test_user_cannot_edit_other_users_habit(auth_client, other_user):
    habit = make_habit(other_user, action="Чужая привычка")

    response = auth_client.get(reverse("habits_web:edit", args=[habit.pk]))

    assert response.status_code == 404


def test_habit_business_rules_reject_reward_and_linked_habit(auth_client, user):
    pleasant = make_habit(user, action="Кофе", is_pleasant=True)
    habit = make_habit(user, action="Зарядка")

    response = auth_client.post(
        reverse("habits_web:edit", args=[habit.pk]),
        {
            "action": "Зарядка",
            "time": "07:00",
            "frequency": 1,
            "time_to_complete": 30,
            "reward": "Кофе",
            "linked_habit": pleasant.pk,
        },
    )

    assert response.status_code == 200
    assert "Нельзя одновременно" in response.content.decode()


def test_create_place_sets_owner(auth_client, user):
    response = auth_client.post(
        reverse("habits_web:place-create"),
        {"name": "Спортзал", "description": "Зал рядом с домом", "is_public": "on"},
    )

    place = Place.objects.get(name="Спортзал")
    assert response.status_code == 302
    assert place.owner == user


def test_send_habit_card_to_telegram(auth_client, user):
    TelegramProfile.objects.create(user=user, telegram_chat_id=123456789)
    habit = make_habit(user, action="Отправить карточку")

    with patch("habits.web_views.send_habit_card") as sender:
        response = auth_client.post(reverse("habits_web:send-telegram", args=[habit.pk]))

    assert response.status_code == 302
    sender.assert_called_once_with(habit)


def test_send_habit_card_without_telegram_profile(auth_client, user):
    habit = make_habit(user)

    with patch("habits.web_views.send_habit_card", side_effect=TelegramNotConfigured):
        response = auth_client.post(
            reverse("habits_web:send-telegram", args=[habit.pk]),
            follow=True,
        )

    assert response.status_code == 200
    assert "Telegram не привязан" in response.content.decode()


def test_send_all_habit_cards_to_telegram(auth_client, user):
    TelegramProfile.objects.create(user=user, telegram_chat_id=123456789)
    make_habit(user, action="Первая карточка")
    make_habit(user, action="Вторая карточка")

    with patch("habits.web_views.send_habit_card") as sender:
        response = auth_client.post(reverse("habits_web:send-telegram-all"))

    assert response.status_code == 302
    assert sender.call_count == 2


def test_cannot_send_other_users_card(auth_client, other_user):
    habit = make_habit(other_user)

    response = auth_client.post(reverse("habits_web:send-telegram", args=[habit.pk]))

    assert response.status_code == 404


def test_duplicate_place_name_is_rejected(auth_client, user):
    Place.objects.create(owner=user, name="Дом")

    response = auth_client.post(
        reverse("habits_web:place-create"),
        {"name": "Дом", "description": "Ещё один дом"},
    )

    assert response.status_code == 200
    assert "уже есть" in response.content.decode()


def test_profile_updates_name_and_telegram(auth_client, user):
    response = auth_client.post(
        reverse("users_web:profile"),
        {
            "save_profile": "1",
            "first_name": "Александр",
            "last_name": "Бачевский",
            "gender": "male",
        },
    )

    user.refresh_from_db()
    assert response.status_code == 302
    assert user.first_name == "Александр"
    assert user.gender == "male"

    response = auth_client.post(
        reverse("users_web:profile"),
        {
            "save_telegram": "1",
            "telegram_chat_id": "123456789",
            "telegram_username": "sky_demo",
            "is_active": "on",
        },
    )

    profile = TelegramProfile.objects.get(user=user)
    assert response.status_code == 302
    assert profile.telegram_chat_id == 123456789
    assert profile.is_active is True
