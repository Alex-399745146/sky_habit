# users/views.py

import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserRegistrationSerializer,
)
from .services import EmailVerificationService

logger = logging.getLogger(__name__)

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

        try:
            EmailVerificationService.send_verification_email(user, request=request)
        except Exception:
            logger.exception("Не удалось отправить письмо подтверждения для %s", user.email)
            detail = "Пользователь зарегистрирован, но письмо не удалось отправить. Проверьте настройки почты."
        else:
            detail = "Пользователь зарегистрирован. Проверьте email и подтвердите адрес."

        return Response({"detail": detail}, status=status.HTTP_201_CREATED)


class EmailVerificationView(APIView):
    """
    Подтверждение email по токену из «письма».
    """

    permission_classes = [AllowAny]

    @extend_schema(
        request=None,
        responses={
            200: OpenApiResponse(
                description="Email успешно подтверждён.",
            ),
            400: OpenApiResponse(
                description="Токен не найден или истёк.",
            ),
        },
    )
    def get(self, request, token):
        user = EmailVerificationService.verify(token)

        if user is None:
            return Response(
                {"detail": "Токен не найден или истёк."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"detail": "Email успешно подтверждён."},
            status=status.HTTP_200_OK,
        )


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
