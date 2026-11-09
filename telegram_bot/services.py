import asyncio
import logging

from django.conf import settings
from django.utils.html import escape
from telegram import Bot

logger = logging.getLogger(__name__)


class TelegramNotConfigured(Exception):
    """У пользователя нет привязанного Telegram-профиля."""


def build_habit_card(habit) -> str:
    """Формирует карточку привычки для Telegram (HTML)."""
    place = escape(habit.place.name) if habit.place else "без места"
    kind = "приятная" if habit.is_pleasant else "полезная"
    frequency = "каждый день" if habit.frequency == 1 else f"раз в {habit.frequency} дн."

    lines = [
        "🟩 <b>SKY HABIT // CARD</b>",
        "",
        f"🎯 <b>{escape(habit.action)}</b>",
        f"🕒 {habit.time.strftime('%H:%M')} · 📍 {place}",
        f"📅 {frequency} · ⏱ {habit.time_to_complete} сек",
        f"🏷 {kind}" + (" · 🌐 публичная" if habit.is_public else ""),
    ]

    if habit.reward:
        lines.append(f"🎁 Вознаграждение: {escape(habit.reward)}")
    if habit.linked_habit:
        lines.append(f"🔗 Связана с: {escape(habit.linked_habit.action)}")

    lines.extend(["", ">_ sky_habit"])
    return "\n".join(lines)


def send_message(chat_id: int, text: str, parse_mode: str | None = None) -> None:
    """Синхронная отправка сообщения через Telegram Bot API."""
    bot_token = settings.TELEGRAM_BOT_TOKEN
    if not bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set.")

    bot = Bot(token=bot_token)

    async def _send() -> None:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)

    asyncio.run(_send())


def send_habit_card(habit, chat_id: int | None = None) -> None:
    """Отправляет карточку привычки в Telegram владельцу или в указанный чат."""
    profile = getattr(habit.owner, "telegram_profile", None)
    if profile is None or not profile.telegram_chat_id:
        raise TelegramNotConfigured("Telegram-профиль не привязан или не указан chat ID.")

    target_chat_id = chat_id or profile.telegram_chat_id
    send_message(target_chat_id, build_habit_card(habit), parse_mode="HTML")
