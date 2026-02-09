import asyncio
import os
import logging

from aiogram import Bot, Dispatcher, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# =========================
# НАСТРОЙКИ
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")  # В variables на Runway
OWNER_ID = 7014418816

if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN не задан в переменных окружения")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# =========================
# ПАМЯТЬ (пока без БД)
# =========================

USERS = {}

def get_user(user_id: int):
    if user_id not in USERS:
        USERS[user_id] = {
            "id": user_id,
            "free": 0,
            "paid": 0,
            "is_owner": user_id == OWNER_ID
        }
    return USERS[user_id]

def can_search(user):
    return user["is_owner"] or user["free"] > 0 or user["paid"] > 0

def consume_search(user):
    if user["is_owner"]:
        return
    if user["free"] > 0:
        user["free"] -= 1
    else:
        user["paid"] -= 1

# =========================
# FSM ПОИСК
# =========================

class SearchForm(StatesGroup):
    menu = State()
    input = State()

FIELDS = {
    "last_name": "Фамилия",
    "first_name": "Имя",
    "birth_year": "Год рождения",
    "city": "Город",
}

def search_keyboard(data: dict):
    buttons = []

    for key, title in FIELDS.items():
        if key in data:
            buttons.append(
                InlineKeyboardButton(
                    text=f"✅ {data[key]}",
                    callback_data=f"edit:{key}"
                )
            )
        else:
            buttons.append(
                InlineKeyboardButton(
                    text=title,
                    callback_data=f"add:{key}"
                )
            )

    buttons.append(InlineKeyboardButton("♻️ Сбросить", callback_data="reset"))
    buttons.append(InlineKeyboardButton("🔍 Искать", callback_data="search"))

    return InlineKeyboardMarkup(
        inline_keyboard=[buttons[i:i+2] for i in range(0, len(buttons), 2)]
    )

# =========================
# /start
# =========================

@dp.message(F.text == "/start")
async def start(message: types.Message, state: FSMContext):
    get_user(message.from_user.id)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Поиск по неполным данным", callback_data="search_start")],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")]
    ])

    await message.answer("🕵️ Sherlock Bot\nВыберите действие:", reply_markup=kb)

# =========================
# СТАРТ ПОИСКА
# =========================

@dp.callback_query(F.data == "search_start")
async def search_start(call: types.CallbackQuery, state: FSMContext):
    user = get_user(call.from_user.id)

    if not can_search(user):
        await call.message.answer("🔒 Недостаточно запросов")
        return

    await state.clear()
    await state.set_state(SearchForm.menu)

    await call.message.answer(
        "Введите любые данные, все поля необязательны:",
        reply_markup=search_keyboard({})
    )

# =========================
# ДОБАВЛЕНИЕ ПОЛЯ
# =========================

@dp.callback_query(F.data.startswith("add:"))
async def add_field(call: types.CallbackQuery, state: FSMContext):
    field = call.data.split(":")[1]

    await state.update_data(current_field=field)
    await state.set_state(SearchForm.input)

    await call.message.answer(
        f"Введите {FIELDS[field].lower()}:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
        ])
    )

# =========================
# ВВОД ТЕКСТА
# =========================

@dp.message()
async def input_value(message: types.Message, state: FSMContext):
    if await state.get_state() != SearchForm.input:
        return

    data = await state.get_data()
    field = data["current_field"]

    await state.update_data({field: message.text})
    await state.set_state(SearchForm.menu)

    new_data = await state.get_data()
    new_data.pop("current_field", None)

    await message.answer(
        "Данные сохранены:",
        reply_markup=search_keyboard(new_data)
    )

# =========================
# СБРОС
# =========================

@dp.callback_query(F.data == "reset")
async def reset(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(SearchForm.menu)

    await call.message.edit_reply_markup(
        reply_markup=search_keyboard({})
    )

# =========================
# ПОИСК (ЗАГЛУШКА)
# =========================

@dp.callback_query(F.data == "search")
async def do_search(call: types.CallbackQuery, state: FSMContext):
    user = get_user(call.from_user.id)

    data = await state.get_data()
    data.pop("current_field", None)

    if not data:
        await call.message.answer("⚠️ Вы не указали ни одного параметра")
        return

    consume_search(user)

    text = "🕵️ Результаты поиска:\n\n"
    for k, v in data.items():
        text += f"• {FIELDS[k]}: {v}\n"

    text += "\nИсточник: открытые данные"

    await call.message.answer(text)

# =========================
# АДМИНКА
# =========================

@dp.message(F.text == "/admin")
async def admin(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return

    await message.answer(
        "🛠 Админка\n"
        "Напиши: /give <user_id> <кол-во>"
    )

@dp.message(F.text.startswith("/give"))
async def give(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return

    try:
        _, uid, amount = message.text.split()
        uid = int(uid)
        amount = int(amount)
    except:
        await message.answer("Формат: /give user_id amount")
        return

    user = get_user(uid)
    user["free"] += amount

    await message.answer(f"✅ Выдано {amount} запросов пользователю {uid}")

# =========================
# ЗАПУСК
# =========================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
