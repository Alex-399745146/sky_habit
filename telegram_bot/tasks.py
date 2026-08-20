# telegram_bot/tasks.py

import asyncio
import logging

from celery import shared_task
from django.conf import settings
from django.utils import timezone
from telegram import Bot

from habits.models import Habit

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
    """Отправка уведомления в Telegram"""

    try:
        habit = Habit.objects.get(id=habit_id)
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

    # Формируем сообщение
    place_name = habit.place.name if habit.place else "Без места"
    habit_type = "приятную" if habit.is_pleasant else "неприятную"
    message = (
        f"🔔 Напоминание о привычке!\n\n"
        f"📍 Место: {place_name}\n"
        f"⏰ Время: {habit.time.strftime('%H:%M')}\n"
        f"🎯 Действие: {habit.action}\n"
        f"💡 Тип: {habit_type}\n"
        f"📅 Периодичность: каждые {habit.frequency} дней\n\n"
        f"Не забудь выполнить! 💪"
    )

    # Отправляем через бота.
    send_telegram_message.delay(profile.telegram_chat_id, message)
    logger.info(f"Notification sent for habit {habit_id}")


@shared_task
def send_telegram_message(chat_id, text):
    """Отправка сообщения в Telegram (через async-бота из Celery)"""

    bot_token = settings.TELEGRAM_BOT_TOKEN
    bot = Bot(token=bot_token)

    async def _send():
        try:
            await bot.send_message(chat_id=chat_id, text=text)
            print(f"[CELERY] Message sent to chat {chat_id}")
        except Exception as e:
            print(f"[CELERY] Failed to send message to {chat_id}: {e}")
            logger.error(f"Failed to send message to {chat_id}: {e}")

    # Запускаем корутину в отдельном event loop
    asyncio.run(_send())
