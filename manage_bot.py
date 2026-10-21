# manage_bot.py

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from telegram_bot.bot import run_bot  # noqa: E402

if __name__ == "__main__":
    run_bot()
