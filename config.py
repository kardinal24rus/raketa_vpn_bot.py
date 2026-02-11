import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден в переменных окружения")

DB_PATH = os.getenv("DB_PATH", "bot_database.sqlite3")
