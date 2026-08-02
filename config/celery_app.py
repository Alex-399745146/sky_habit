# config/celery_app.py

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery(
    "sky_habit",
    broker="redis://127.0.0.1:6379/0",  # Явно указываем Redis
    backend="redis://127.0.0.1:6379/0",  # Явно указываем Redis
)

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

# Расписание для Celery Beat
app.conf.beat_schedule = {
    "send-daily-reminders-every-minute": {
        "task": "telegram_bot.tasks.send_daily_reminders",
        # Потом, когда всё заработает, можно вернуть, например, crontab(hour=9, minute=0).
        "schedule": crontab(minute="*"),  # каждую минуту
    },
}
