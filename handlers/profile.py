from aiogram import Router
from aiogram.types import CallbackQuery
from keyboards import bottom_keyboard
from database import DB_PATH
import sqlite3

router = Router()

@router.callback_query(lambda c: c.data == "profile")
async def profile(callback: CallbackQuery):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT balance, search_count FROM users WHERE telegram_id = ?", (callback.from_user.id,))
    row = cursor.fetchone()
    conn.close()

    balance = row[0] if row else 0
    search_count = row[1] if row else 0

    text = f"Ваш ID: {callback.from_user.id}\nДоступно поисков: {search_count}\nБаланс: ${balance:.2f}"
    await callback.message.answer(text, reply_markup=bottom_keyboard())
    await callback.answer()
