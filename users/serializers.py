# users/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from pathlib import Path
import json
import uuid
from datetime import timedelta

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Сериализатор регистрации пользователя.
    После создания пользователя помечаем is_verified=False.
    """

    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name"]
        extra_kwargs = {
            "first_name": {"required": False},
            "last_name": {"required": False},
        }

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data["email"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            is_verified=False,
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class EmailVerificationService:
    """
    Заглушка для отправки email: сохраняет JSON в tmp/emails/.
    """

    @staticmethod
    def send_verification_email(email: str, token: str):
        tmp_dir = Path(settings.BASE_DIR) / "tmp" / "emails"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        payload = {
            "email": email,
            "token": token,
            "type": "verification",
        }

        filename = f"verify_{uuid.uuid4().hex}.json"
        file_path = tmp_dir / filename

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        return file_path