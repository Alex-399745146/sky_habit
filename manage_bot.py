# manage_bot.py

import os

import django

from telegram_bot.bot import run_bot

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()
    run_bot()
