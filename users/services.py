import json
import uuid
from pathlib import Path

from django.conf import settings


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
