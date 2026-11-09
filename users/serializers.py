# users/serializers.py

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .services import EmailVerificationService

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


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Сериализатор запроса сброса пароля.
    """

    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Сериализатор подтверждения сброса пароля (новый пароль).
    """

    new_password = serializers.CharField(min_length=6, write_only=True)
