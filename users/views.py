# users/views.py

import json
import uuid
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .serializers import (
    EmailVerificationService,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserRegistrationSerializer,
)

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """
    Регистрация пользователя.
    После регистрации отправляется «письмо» с токеном верификации (заглушка).
    """

    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Генерация токена верификации
        token = str(uuid.uuid4())

        # Сохранение токена в БД (можно в отдельной модели, пока просто в памяти или кэше)
        # Для простоты — просто отправляем «письмо»
        EmailVerificationService.send_verification_email(user.email, token)

        return Response(
            {"detail": "Пользователь зарегистрирован. Проверьте tmp/emails/ для токена верификации."},
            status=status.HTTP_201_CREATED,
        )


class EmailVerificationView(generics.GenericAPIView):
    """
    Подтверждение email по токену из «письма».
    """

    permission_classes = [AllowAny]

    def get(self, request, token):
        tmp_dir = Path(settings.BASE_DIR) / "tmp" / "emails"
        found = False

        for file_path in tmp_dir.glob("verify_*.json"):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("token") == token:
                    user = User.objects.get(email=data["email"])
                    user.is_verified = True
                    user.save()
                    found = True
                    break

        if not found:
            return Response(
                {"detail": "Токен не найден или истёк."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"detail": "Email успешно подтверждён."})


class PasswordResetRequestView(generics.GenericAPIView):
    """
    Запрос сброса пароля: генерация токена и «отправка» письма (заглушка).
    """

    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # В целях безопасности не сообщаем, существует ли пользователь
            return Response(
                {"detail": "Если пользователь с таким email существует, ему отправлено письмо."},
                status=status.HTTP_200_OK,
            )

        # Генерация токена и uid
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # «Отправка» письма (заглушка)
        EmailVerificationService.send_password_reset_email(user.email, token, uid)

        return Response(
            {"detail": "Если пользователь с таким email существует, ему отправлено письмо."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(generics.GenericAPIView):
    """
    Подтверждение сброса пароля: установка нового пароля по токену.
    """

    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]

    def post(self, request, uid, token):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            uid = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=uid)
        except (ValueError, User.DoesNotExist):
            return Response(
                {"detail": "Неверный токен или пользователь не найден."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {"detail": "Токен неверен или истёк."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Установка нового пароля
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response(
            {"detail": "Пароль успешно изменён."},
            status=status.HTTP_200_OK,
        )
