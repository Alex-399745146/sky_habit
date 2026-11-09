import datetime

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from habits.models import Habit, Place
from telegram_bot.models import TelegramProfile

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


def test_register_creates_user_and_logs_in(client):
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
    assert client.get(reverse("users_web:profile")).status_code == 200


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
        {"save_profile": "1", "first_name": "Александр", "last_name": "Бачевский"},
    )

    user.refresh_from_db()
    assert response.status_code == 302
    assert user.first_name == "Александр"

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
