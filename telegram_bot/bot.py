# telegram_bot/bot.py

from asgiref.sync import sync_to_async
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from .models import TelegramProfile

logger = logging.getLogger(__name__)
User = get_user_model()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        return

    telegram_id = update.effective_user.id
    username = update.effective_user.username or ""

    async def get_or_create_profile():
        try:
            profile = await sync_to_async(TelegramProfile.objects.get)(telegram_id=telegram_id)
            profile.telegram_username = username
            await sync_to_async(profile.save)()
            return True
        except TelegramProfile.DoesNotExist:
            await sync_to_async(TelegramProfile.objects.create)(
                telegram_id=telegram_id,
                telegram_username=username,
            )
            return False

    exists = await get_or_create_profile()
    message = (
    )

    await update.message.reply_text(
        f"{message}\n\n"
        f"Доступные команды:\n"
        f"/link — привязать аккаунт\n"
        f"/help — помощь\n"
        f"/stop — отключить уведомления\n"
        f"/start_notified — включить уведомления"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""

    await update.message.reply_text(
        "🤖 Бот для напоминаний о привычках\n\n"
        "Команды:\n"
        "/start — начать использование\n"
        "/link — привязать аккаунт Sky Habit\n"
        "/help — эта справка\n"
        "/stop — отключить уведомления\n"
        "/start_notified — включить уведомления"
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /stop"""
        return

    telegram_id = update.effective_user.id

    try:
        profile = TelegramProfile.objects.get(telegram_id=telegram_id)
        profile.notified = False
        profile.save()
        await update.message.reply_text("❌ Уведомления отключены.")
    except TelegramProfile.DoesNotExist:
        await update.message.reply_text("Профиль не найден. Используйте /start")


async def start_notified(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start_notified"""

        return

    telegram_id = update.effective_user.id

    try:
        profile = TelegramProfile.objects.get(telegram_id=telegram_id)
        profile.notified = True
        profile.save()
        await update.message.reply_text("✅ Уведомления включены.")
    except TelegramProfile.DoesNotExist:
        await update.message.reply_text("Профиль не найден. Используйте /start")


async def link_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /link"""

        return

    telegram_id = update.effective_user.id

    # Получаем или создаём профиль в отдельном потоке
    try:
        profile = await sync_to_async(TelegramProfile.objects.get)(telegram_id=telegram_id)
    except TelegramProfile.DoesNotExist:
        return

    # Если уже привязан
    if profile.user:
        return

    # Если есть аргументы (email)
    if context.args:
        email = context.args[0]

        try:
            user = await sync_to_async(User.objects.get)(email=email)
        except User.DoesNotExist:
            return

        profile.user = user
        await sync_to_async(profile.save)()
    else:
        await update.message.reply_text(
        )


def run_bot():
    """Запуск бота"""

    bot_token = settings.TELEGRAM_BOT_TOKEN
    application = Application.builder().token(bot_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("start_notified", start_notified))
    application.add_handler(CommandHandler("link", link_command))

    logger.info("Telegram bot started")
    application.run_polling(allowed_updates=Update.ALL_TYPES)