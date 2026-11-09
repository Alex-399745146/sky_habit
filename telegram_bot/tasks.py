# telegram_bot/tasks.py

import logging

from celery import shared_task
from django.utils import timezone

from habits.models import Habit

from .services import build_habit_card, send_message

logger = logging.getLogger(__name__)


@shared_task
def send_daily_reminders():
    """Проверка привычек по времени."""

    now = timezone.localtime()
    current_time = now.time().replace(second=0, microsecond=0)

    habits = Habit.objects.filter(owner__telegram_profile__is_active=True)

    print(f"[CELERY] Checking habits for time {current_time.strftime('%H:%M')}")

    for habit in habits:
        habit_time = getattr(habit, "time", None)
        if not habit_time:
            continue

        habit_time_clean = habit_time.replace(second=0, microsecond=0)

        if habit_time_clean == current_time:
            print(f"[CELERY] Sending notification for habit {habit.id} ({habit.action}) at {current_time}")
            send_telegram_notification.delay(habit.id)


@shared_task
def send_telegram_notification(habit_id):
    """Отправка карточки привычки в Telegram."""

    try:
        habit = Habit.objects.select_related("owner", "place", "linked_habit").get(id=habit_id)
    except Habit.DoesNotExist:
        logger.warning(f"Habit {habit_id} not found")
        return

    if not hasattr(habit.owner, "telegram_profile"):
        logger.warning(f"User {habit.owner.email} has no Telegram profile")
        return

    profile = habit.owner.telegram_profile
    if not profile.is_active:
        logger.info(f"Notifications disabled for user {profile.user.email}")
        return

    card = build_habit_card(habit)
    send_telegram_message.delay(profile.telegram_chat_id, card, "HTML")
    logger.info(f"Notification sent for habit {habit_id}")


@shared_task
def send_telegram_message(chat_id, text, parse_mode=None):
    """Отправка сообщения в Telegram через Bot API."""

    try:
        send_message(chat_id, text, parse_mode=parse_mode)
        print(f"[CELERY] Message sent to chat {chat_id}")
    except Exception as error:
        print(f"[CELERY] Failed to send message to {chat_id}: {error}")
        logger.error(f"Failed to send message to {chat_id}: {error}")
