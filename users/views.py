# users/views.py

from pathlib import Path
import json
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .serializers import UserRegistrationSerializer, EmailVerificationService

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
        # В реальном проекте здесь была бы проверка токена в БД/кэше
        # Для заглушки — просто ищем файл в tmp/emails/
        from pathlib import Path
        import json

        tmp_dir = Path(settings.BASE_DIR) / "tmp" / "emails"
        found = False

        for file_path in tmp_dir.glob("verify_*.json"):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("token") == token:
                    # Находим пользователя по email
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