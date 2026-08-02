# users/test_users.py

"""
Тесты для приложения users.
"""

import json
from pathlib import Path

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from users.models import User
from users.serializers import (
    EmailVerificationService,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserRegistrationSerializer,
)

UserModel = get_user_model()


@pytest.fixture
def api_client():
    """Создание API клиента."""
    return APIClient()


@pytest.fixture
def user(db):
    """Создание тестового пользователя."""
    return UserModel.objects.create_user(
        email="user@example.com", password="testpass123", first_name="Test", last_name="User"
    )


@pytest.mark.django_db
class TestUserModel:
    """Тесты модели User."""

    def test_user_creation(self):
        """Тест создания пользователя."""
        user = UserModel.objects.create_user(
            email="newuser@example.com", password="password123", first_name="John", last_name="Doe"
        )
        assert user.email == "newuser@example.com"
        assert user.first_name == "John"
        assert user.is_verified is False
        assert user.check_password("password123")

    def test_user_str(self):
        """Тест строкового представления."""
        user = UserModel.objects.create_user(username="strtest", email="strtest@example.com", password="password123")
        assert str(user) == "strtest@example.com"

    def test_user_str_no_email(self):
        """Тест строкового представления, если email пустой (технический случай)."""
        user = UserModel.objects.create_user(
            email="noemail@example.com",
            password="password123",
            username="noemail",
        )
        # Принудительно очищаем email (только для теста, чтобы проверить __str__)
        user.email = ""
        assert str(user) == f"User #{user.pk}"

    def test_user_authentication_by_email(self):
        """Тест аутентификации по email."""
        user = UserModel.objects.create_user(username="authuser", email="auth@example.com", password="securepass")

        # USERNAME_FIELD должен быть email
        assert UserModel.USERNAME_FIELD == "email"

        # Проверка что username не уникален
        user2 = UserModel.objects.create_user(
            username="duplicate_username",
            email="another@example.com",
            password="securepass",
        )
        assert user2.username == "duplicate_username"

        # Реальная проверка аутентификации по email
        from django.contrib.auth import authenticate

        authenticated_user = authenticate(username="auth@example.com", password="securepass")
        assert authenticated_user == user


@pytest.mark.django_db
class TestUserRegistrationSerializer:
    """Тесты сериализатора регистрации."""

    def test_registration_serializer_valid(self):
        """Тест валидной регистрации."""
        data = {"email": "register@example.com", "password": "securepass123", "first_name": "New", "last_name": "User"}
        serializer = UserRegistrationSerializer(data=data)
        assert serializer.is_valid()

        user = serializer.save()
        assert user.email == "register@example.com"
        assert user.is_verified is False
        assert user.check_password("securepass123")

    def test_registration_serializer_minimal(self):
        """Тест минимальной регистрации."""
        data = {"email": "minimal@example.com", "password": "password123"}
        serializer = UserRegistrationSerializer(data=data)
        assert serializer.is_valid()

        user = serializer.save()
        assert user.first_name == ""
        assert user.last_name == ""

    def test_registration_serializer_short_password(self):
        """Тест слишком короткого пароля."""
        data = {"email": "short@example.com", "password": "12345"}  # 5 символов, минимум 6
        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert "password" in serializer.errors

    def test_registration_serializer_invalid_email(self):
        """Тест невалидного email."""
        data = {"email": "invalid-email", "password": "password123"}
        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert "email" in serializer.errors


@pytest.mark.django_db
class TestPasswordResetSerializers:
    """Тесты сериализаторов сброса пароля."""

    def test_password_reset_request_valid(self):
        """Тест запроса сброса пароля."""
        data = {"email": "reset@example.com"}
        serializer = PasswordResetRequestSerializer(data=data)
        assert serializer.is_valid()

    def test_password_reset_request_invalid_email(self):
        """Тест невалидного email для сброса."""
        data = {"email": "not-an-email"}
        serializer = PasswordResetRequestSerializer(data=data)
        assert not serializer.is_valid()

    def test_password_reset_confirm_valid(self):
        """Тест подтверждения сброса пароля."""
        data = {"new_password": "newsecurepass123"}
        serializer = PasswordResetConfirmSerializer(data=data)
        assert serializer.is_valid()

    def test_password_reset_confirm_short_password(self):
        """Тест короткого нового пароля."""
        data = {"new_password": "12345"}
        serializer = PasswordResetConfirmSerializer(data=data)
        assert not serializer.is_valid()


class TestEmailVerificationService:
    """Тесты сервиса верификации email."""

    def test_send_verification_email(self):
        """Тест отправки письма верификации."""

        file_path = EmailVerificationService.send_verification_email("verify@example.com", "test-token-123")

        assert file_path.exists()

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["email"] == "verify@example.com"
        assert data["token"] == "test-token-123"
        assert data["type"] == "verification"

    def test_send_password_reset_email(self):
        """Тест отправки письма сброса пароля."""

        file_path = EmailVerificationService.send_password_reset_email(
            "reset@example.com", "reset-token-456", "encoded-uid"
        )

        assert file_path.exists()

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["email"] == "reset@example.com"
        assert data["token"] == "reset-token-456"
        assert data["uid"] == "encoded-uid"
        assert data["type"] == "password_reset"


@pytest.mark.django_db
class TestUserRegistrationAPI:
    """Интеграционные тесты API пользователей."""

    def test_register_user(self, api_client):
        """Тест регистрации пользователя через API."""
        data = {
            "email": "api-register@example.com",
            "password": "apipass123",
            "first_name": "API",
            "last_name": "User",
        }

        response = api_client.post("/api/users/register/", data)
        assert response.status_code == 201
        assert "Пользователь зарегистрирован" in response.data["detail"]

    def test_register_duplicate_email(self, api_client, user):
        """Тест регистрации с существующим email."""
        data = {"email": user.email, "password": "anotherpass123"}

        response = api_client.post("/api/users/register/", data)
        assert response.status_code == 400

    def test_email_verification(self, api_client, db):
        """Тест верификации email."""
        # Создаем пользователя
        UserModel.objects.create_user(username="verifyuser", email="verify-api@example.com", password="pass123")

        # Верифицируем
        response = api_client.get("/api/users/verify/api-verify-token/")
        assert response.status_code == 200
        assert "Email успешно подтверждён" in response.data["detail"]

    def test_email_verification_invalid_token(self, api_client):
        """Тест верификации с невалидным токеном."""
        response = api_client.get("/api/users/verify/invalid-token/")
        assert response.status_code == 400

    def test_password_reset_request(self, api_client, user):
        """Тест запроса сброса пароля."""
        data = {"email": user.email}

        response = api_client.post("/api/users/password-reset/", data)
        assert response.status_code == 200

    def test_password_reset_nonexistent_email(self, api_client):
        """Тест запроса сброса для несуществующего email."""
        data = {"email": "nonexistent@example.com"}

        response = api_client.post("/api/users/password-reset/", data)
        assert response.status_code == 200
        assert "Если пользователь с таким email существует" in response.data["detail"]

    def test_password_reset_confirm(self, api_client, user):
        """Тест подтверждения сброса пароля."""
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        data = {"new_password": "newpassword123"}

        response = api_client.post(f"/api/users/password-reset-confirm/{uid}/{token}/", data)
        assert response.status_code == 200
        assert "Пароль успешно изменён" in response.data["detail"]

    def test_password_reset_confirm_invalid_token(self, api_client, user):
        """Тест сброса пароля с невалидным токеном."""
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        uid = urlsafe_base64_encode(force_bytes(user.pk))

        data = {"new_password": "newpassword123"}

        response = api_client.post(f"/api/users/password-reset-confirm/{uid}/invalid-token/", data)
        assert response.status_code == 400
