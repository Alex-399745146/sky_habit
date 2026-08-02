# habits/test_models.py

"""
Тесты для приложения habits.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from habits.models import Habit, Place
from habits.pagination import HabitPagination
from habits.permissions import (
    IsOwnerOrReadOnly,
    IsOwnerOrReadOnlyForPlace,
    IsOwnerReadWrite,
)
from habits.serializers import HabitSerializer, PlaceSerializer

User = get_user_model()


@pytest.fixture
def user(db):
    """Создание тестового пользователя."""
    return User.objects.create_user(
        username="testuser", email="test@example.com", password="testpass123", first_name="Test", last_name="User"
    )


@pytest.fixture
def user2(db):
    """Создание второго тестового пользователя."""
    return User.objects.create_user(
        username="testuser2", email="test2@example.com", password="testpass123", first_name="Test2", last_name="User2"
    )


@pytest.fixture
def api_client():
    """Создание API клиента."""
    return APIClient()


@pytest.fixture
def place(user):
    """Создание тестового места."""
    return Place.objects.create(owner=user, name="Дом", description="Мое любимое место дома", is_public=False)


@pytest.fixture
def habit(user, place):
    """Создание тестовой привычки."""
    return Habit.objects.create(
        owner=user,
        place=place,
        time="08:00:00",
        action="Делать зарядку",
        is_pleasant=False,
        frequency=1,
        time_to_complete=60,
        is_public=False,
    )


class TestPlaceModel:
    """Тесты модели Place."""

    def test_place_creation(self, user):
        """Тест создания места."""
        place = Place.objects.create(owner=user, name="Офис", description="Рабочее место", is_public=True)
        assert place.name == "Офис"
        assert place.owner == user
        assert place.is_public is True
        assert str(place) == "Офис (test@example.com)"

    def test_place_unique_together(self, user, place):
        """Тест уникальности имени места для владельца."""
        with pytest.raises(Exception):
            Place.objects.create(owner=user, name="Дом", description="Дубликат", is_public=False)


class TestHabitModel:
    """Тесты модели Habit."""

    def test_habit_creation(self, user, place):
        """Тест создания привычки."""
        habit = Habit.objects.create(
            owner=user,
            place=place,
            time="07:00:00",
            action="Бегать по утрам",
            is_pleasant=False,
            frequency=3,
            time_to_complete=30,
            is_public=True,
        )
        assert habit.action == "Бегать по утрам"
        assert habit.owner == user
        assert habit.is_public is True
        assert str(habit) == "Бегать по утрам (test@example.com)"

    def test_habit_validation_reward_and_linked(self, user):
        """Тест валидации: нельзя одновременно reward и linked_habit."""
        pleasant_habit = Habit.objects.create(
            owner=user, time="09:00:00", action="Приятная привычка", is_pleasant=True, frequency=1, time_to_complete=15
        )

        habit = Habit(
            owner=user,
            time="08:00:00",
            action="Полезная привычка",
            is_pleasant=False,
            frequency=1,
            time_to_complete=30,
            reward="Кофе",
            linked_habit=pleasant_habit,
        )

        with pytest.raises(Exception):
            habit.full_clean()

    def test_habit_validation_pleasant_with_reward(self, user):
        """Тест валидации: у приятной привычки не может быть reward."""
        habit = Habit(
            owner=user,
            time="08:00:00",
            action="Приятная привычка",
            is_pleasant=True,
            frequency=1,
            time_to_complete=30,
            reward="Награда",
        )

        with pytest.raises(Exception):
            habit.full_clean()

    def test_habit_validation_linked_not_pleasant(self, user):
        """Тест валидации: linked_habit должна быть приятной."""
        not_pleasant = Habit.objects.create(
            owner=user,
            time="08:00:00",
            action="Неприятная привычка",
            is_pleasant=False,
            frequency=1,
            time_to_complete=30,
        )

        habit = Habit(
            owner=user,
            time="09:00:00",
            action="Полезная привычка",
            is_pleasant=False,
            frequency=1,
            time_to_complete=30,
            linked_habit=not_pleasant,
        )

        with pytest.raises(Exception):
            habit.full_clean()


class TestPlaceSerializer:
    """Тесты сериализатора Place."""

    def test_place_serializer(self, user, place):
        """Тест сериализации места."""
        serializer = PlaceSerializer(place)
        data = serializer.data

        assert data["name"] == "Дом"
        assert data["owner"] == user.id
        assert "created_at" in data

    def test_place_serializer_create(self, user):
        """Тест создания места через сериализатор."""
        data = {"name": "Спортзал", "description": "Место для тренировок", "is_public": True}
        serializer = PlaceSerializer(data=data)
        assert serializer.is_valid()
        place = serializer.save(owner=user)
        assert place.name == "Спортзал"
        assert place.owner == user


class TestHabitSerializer:
    """Тесты сериализатора Habit."""

    def test_habit_serializer(self, user, place, habit):
        """Тест сериализации привычки."""
        serializer = HabitSerializer(habit)
        data = serializer.data

        assert data["action"] == "Делать зарядку"
        assert data["owner"] == user.id
        assert "time" in data

    def test_habit_serializer_validation_reward_and_linked(self, user, habit):
        """Тест валидации сериализатора: reward и linked_habit."""
        data = {
            "time": "10:00:00",
            "action": "Тестовая привычка",
            "is_pleasant": False,
            "frequency": 1,
            "time_to_complete": 30,
            "reward": "Награда",
            "linked_habit": habit.id,
        }
        serializer = HabitSerializer(data=data)
        assert not serializer.is_valid()
        assert "Нельзя одновременно указать вознаграждение и связанную привычку" in str(serializer.errors)

    def test_habit_serializer_validation_pleasant_with_reward(self, habit):
        """Тест валидации: приятная привычка с reward."""
        data = {
            "time": "10:00:00",
            "action": "Приятная привычка",
            "is_pleasant": True,
            "frequency": 1,
            "time_to_complete": 30,
            "reward": "Награда",
        }
        serializer = HabitSerializer(data=data)
        assert not serializer.is_valid()
        assert "У приятной привычки не может быть вознаграждения" in str(serializer.errors)


class TestPermissions:
    """Тесты разрешений."""

    def test_is_owner_or_read_only_safe_methods(self, user, place):
        """Тест разрешения для безопасных методов."""
        permission = IsOwnerOrReadOnly()

        class MockRequest:
            method = "GET"

        result = permission.has_object_permission(MockRequest(), None, place)
        assert result is True

    def test_is_owner_or_read_only_owner(self, user, place):
        """Тест разрешения для владельца."""
        permission = IsOwnerOrReadOnly()

        class MockRequest:
            method = "PUT"
            user = place.owner

        result = permission.has_object_permission(MockRequest(), None, place)
        assert result is True

    def test_is_owner_or_read_only_not_owner(self, user, user2, place):
        """Тест разрешения для не владельца."""
        permission = IsOwnerOrReadOnly()

        class MockRequest:
            method = "PUT"
            user = user2

        result = permission.has_object_permission(MockRequest(), None, place)
        assert result is False

    def test_is_owner_or_read_only_for_place_public(self, user, user2, place):
        """Тест разрешения для публичного места."""
        place.is_public = True
        place.save()

        permission = IsOwnerOrReadOnlyForPlace()

        class MockRequest:
            method = "GET"

        result = permission.has_object_permission(MockRequest(), None, place)
        assert result is True

    def test_is_owner_read_write(self, user, place):
        """Тест разрешения IsOwnerReadWrite."""
        permission = IsOwnerReadWrite()

        class MockRequest:
            method = "DELETE"
            user = place.owner

        result = permission.has_object_permission(MockRequest(), None, place)
        assert result is True


class TestHabitPagination:
    """Тесты пагинации."""

    def test_pagination_defaults(self):
        """Тест значений по умолчанию."""
        pagination = HabitPagination()
        assert pagination.default_limit == 5
        assert pagination.max_limit == 50


class TestPlaceAPI:
    """Интеграционные тесты API для мест."""

    def test_create_place(self, api_client, user):
        """Тест создания места через API."""
        api_client.force_authenticate(user=user)

        data = {"name": "Парк", "description": "Место для прогулок", "is_public": True}

        response = api_client.post("/api/places/", data)
        assert response.status_code == 201
        assert response.data["name"] == "Парк"

    def test_list_places(self, api_client, user, place):
        """Тест получения списка мест."""
        api_client.force_authenticate(user=user)

        response = api_client.get("/api/places/")
        assert response.status_code == 200
        assert len(response.data["results"]) == 1

    def test_delete_place_not_owner(self, api_client, user, user2, place):
        """Тест удаления места не владельцем."""
        api_client.force_authenticate(user=user2)

        response = api_client.delete(f"/api/places/{place.id}/")
        assert response.status_code == 404


class TestHabitAPI:
    """Интеграционные тесты API для привычек."""

    def test_create_habit(self, api_client, user, place):
        """Тест создания привычки через API."""
        api_client.force_authenticate(user=user)

        data = {
            "place": place.id,
            "time": "06:00:00",
            "action": "Медитация",
            "is_pleasant": False,
            "frequency": 1,
            "time_to_complete": 15,
            "is_public": False,
        }

        response = api_client.post("/api/habits/", data)
        assert response.status_code == 201
        assert response.data["action"] == "Медитация"

    def test_list_habits(self, api_client, user, habit):
        """Тест получения списка привычек."""
        api_client.force_authenticate(user=user)

        response = api_client.get("/api/habits/")
        assert response.status_code == 200
        assert "results" in response.data

    def test_public_habits(self, api_client, user, habit):
        """Тест получения публичных привычек."""
        habit.is_public = True
        habit.save()

        response = api_client.get("/api/habits/public/")
        assert response.status_code == 200
        assert len(response.data["results"]) == 1

    def test_create_habit_unauthenticated(self, api_client):
        """Тест создания привычки без аутентификации."""
        response = api_client.post("/api/habits/", {})
        assert response.status_code == 401
