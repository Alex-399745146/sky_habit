import json
import logging
import uuid
from datetime import timedelta
from pathlib import Path
from typing import cast
from urllib.parse import urljoin

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone

from .models import EmailVerificationToken

logger = logging.getLogger(__name__)

VERIFICATION_TOKEN_TTL = timedelta(hours=24)


class EmailVerificationService:
    """Подтверждение email: одноразовый токен в БД и письмо со ссылкой."""

    @staticmethod
    def issue_verification_token(user) -> EmailVerificationToken:
        return cast(
            EmailVerificationToken,
            EmailVerificationToken.objects.create(
                user=user,
                token=uuid.uuid4().hex,
                expires_at=timezone.now() + VERIFICATION_TOKEN_TTL,
            ),
        )

    @staticmethod
    def build_verification_url(token: str, request=None, base_url: str | None = None) -> str:
        path = str(reverse("users_web:verify", args=[token]))
        if request is not None:
            return str(request.build_absolute_uri(path))

        base = base_url or getattr(settings, "SITE_URL", "") or "http://localhost:8000"
        return str(urljoin(base.rstrip("/") + "/", path.lstrip("/")))

    @classmethod
    def send_verification_email(cls, user, request=None, base_url: str | None = None) -> EmailVerificationToken:
        token = cls.issue_verification_token(user)
        verify_url = cls.build_verification_url(token.token, request=request, base_url=base_url)

        subject = "Подтверждение email — Sky Habit"
        message = (
            "Здравствуйте!\n\n"
            "Вы зарегистрировались в Sky Habit.\n"
            f"Подтвердите email по ссылке (действует 24 часа):\n{verify_url}\n\n"
            "Если вы не регистрировались, просто проигнорируйте это письмо.\n"
        )
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return token

    @staticmethod
    def verify(token: str):
        try:
            verification = EmailVerificationToken.objects.select_related("user").get(token=token)
        except EmailVerificationToken.DoesNotExist:
            return None

        if verification.is_expired:
            verification.delete()
            return None

        user = verification.user
        if not user.is_verified:
            user.is_verified = True
            user.save(update_fields=["is_verified"])

        EmailVerificationToken.objects.filter(user=user).delete()
        return user

    # --- Заглушка сброса пароля (будет переведена на email отдельной задачей). ---

    @staticmethod
    def send_password_reset_email(email: str, token: str, uid: str):
        tmp_dir = Path(settings.BASE_DIR) / "tmp" / "emails"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        payload = {
            "email": email,
            "token": token,
            "uid": uid,
            "type": "password_reset",
        }

        filename = f"reset_{uuid.uuid4().hex}.json"
        file_path = tmp_dir / filename

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        return file_path
