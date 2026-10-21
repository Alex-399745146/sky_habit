import logging

from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth import get_user_model
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from .models import TelegramProfile

logger = logging.getLogger(__name__)
User = get_user_model()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Создаёт или обновляет Telegram-профиль."""
    if update.effective_user is None or update.effective_chat is None or update.message is None:
        return

    chat_id = update.effective_chat.id
    username = update.effective_user.username or ""

    try:
        profile = await sync_to_async(TelegramProfile.objects.get)(telegram_chat_id=chat_id)
        profile.telegram_chat_id = chat_id
        profile.telegram_username = username
        await sync_to_async(profile.save)()
        message = "С возвращением! Ваш Telegram-профиль обновлён."
    except TelegramProfile.DoesNotExist:
        await sync_to_async(TelegramProfile.objects.create)(
            telegram_chat_id=chat_id,
            telegram_username=username,
        )
        message = "Добро пожаловать! Ваш Telegram-профиль создан."

    await update.message.reply_text(
        f"{message}\n\n"
        "Доступные команды:\n"
        "/link <email> — привязать аккаунт\n"
        "/help — помощь\n"
        "/stop — отключить уведомления\n"
        "/start_notified — включить уведомления"
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Отправляет справку."""
    if update.message is None:
        return

    await update.message.reply_text(
        "🤖 Бот для напоминаний о привычках\n\n"
        "Команды:\n"
        "/start — начать использование\n"
        "/link <email> — привязать аккаунт Sky Habit\n"
        "/help — эта справка\n"
        "/stop — отключить уведомления\n"
        "/start_notified — включить уведомления"
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отключает уведомления."""
    if update.effective_user is None or update.effective_chat is None or update.message is None:
        return

    try:
        profile = await sync_to_async(TelegramProfile.objects.get)(telegram_chat_id=update.effective_chat.id)
        profile.is_active = False
        await sync_to_async(profile.save)()
        await update.message.reply_text("❌ Уведомления отключены.")
    except TelegramProfile.DoesNotExist:
        await update.message.reply_text("Профиль не найден. Используйте /start.")


async def start_notified(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Включает уведомления."""
    if update.effective_user is None or update.effective_chat is None or update.message is None:
        return

    try:
        profile = await sync_to_async(TelegramProfile.objects.get)(telegram_chat_id=update.effective_chat.id)
        profile.is_active = True
        await sync_to_async(profile.save)()
        await update.message.reply_text("✅ Уведомления включены.")
    except TelegramProfile.DoesNotExist:
        await update.message.reply_text("Профиль не найден. Используйте /start.")


async def link_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Привязывает Telegram-профиль к пользователю по email."""
    if update.effective_user is None or update.effective_chat is None or update.message is None:
        return

    if not context.args:
        await update.message.reply_text("Использование: /link ваш_email@example.com")
        return

    email = context.args[0]

    try:
        profile = await sync_to_async(TelegramProfile.objects.get)(telegram_chat_id=update.effective_chat.id)
    except TelegramProfile.DoesNotExist:
        await update.message.reply_text("Сначала используйте /start, чтобы создать Telegram-профиль.")
        return

    if profile.user_id:
        await update.message.reply_text("Аккаунт уже привязан.")
        return

    try:
        user = await sync_to_async(User.objects.get)(email=email)
    except User.DoesNotExist:
        await update.message.reply_text("Пользователь с таким email не найден.")
        return

    profile.user = user
    await sync_to_async(profile.save)()
    await update.message.reply_text("✅ Аккаунт успешно привязан.")


def run_bot() -> None:
    """Запускает Telegram-бота в polling-режиме."""
    bot_token = settings.TELEGRAM_BOT_TOKEN

    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set.")

    application = Application.builder().token(bot_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("start_notified", start_notified))
    application.add_handler(CommandHandler("link", link_command))

    logger.info("Telegram bot started")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
