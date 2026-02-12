import sqlite3
from config import DB_PATH

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Создаем таблицу пользователей, если не существует
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,
        language TEXT DEFAULT 'ru',
        balance REAL DEFAULT 0,
        search_count INTEGER DEFAULT 0,
        registration_date TEXT
    )
    """)
    conn.commit()
    conn.close()