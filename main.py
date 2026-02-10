import asyncio
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# =====================
# CONFIG
# =====================
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 7014418816

# =====================
# USER MODEL (in-memory)
# =====================
USERS = {}

def get_user(user_id: int):
    if user_id not in USERS:
        USERS[user_id] = {
            "role": "user",   # owner | whitelist | user
            "balance": 0,
            "free": 0,
        }
    return USERS[user_id]

def can_search(user: dict) -> bool:
    if user["role"] == "owner":
        return True

    if user["balance"] > 0:
        user["balance"] -= 1
        return True

    if user["free"] > 0:
        user["free"] -= 1
        return True

    return False

# =====================
# KEYBOARDS
# =====================
bottom_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📂 Показать меню"),
            KeyboardButton(text="👤 Выбрать пользователя")
        ]
    ],
    resize_keyboard=True
)

main_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 Поиск по неполным данным")],
        [KeyboardButton(text="👤 Мой профиль")],
        [KeyboardButton(text="💰 Пополнить баланс")],
    ],
    resize_keyboard=True
)

payment_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💳 CryptoBot")],
        [KeyboardButton(text="⬅️ Назад")],
    ],
    resize_keyboard=True
)

# =====================
# SEARCH FSM
# =====================
class SearchState(StatesGroup):
    fill_form = State()
    waiting_value = State()

FIELDS = [
    ("Фамилия", "last_name"),
    ("Имя", "first_name"),
    ("Никнейм", "nickname"),
]

FIELDS_MAP = {title: key for title, key in FIELDS}

def search_keyboard(form: dict):
    keyboard = []
    for title, key in FIELDS:
        if key in form:
            keyboard.append([KeyboardButton(text=f"{form[key]} ✅")])
        else:
            keyboard.append([KeyboardButton(text=title)])

    keyboard.append([
        KeyboardButton(text="🔄 Сбросить"),
        KeyboardButton(text="🔍 Искать"),
    ])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Отмена")]],
    resize_keyboard=True
)

# =====================
# MOCK SEARCH
# =====================
def mock_search(form: dict):
    return [
        {
            "type": "Личность",
            "value": f"{form.get('last_name','Иванов')} {form.get('first_name','Иван')}",
            "source": "mock",
            "confidence": 80
        },
        {
            "type": "Соцсети",
            "value": f"vk.com/{form.get('nickname','example')}",
            "source": "mock",
            "confidence": 70
        }
    ]

# =====================
# ROUTERS
# =====================
router = Router()

START_TEXT = (
    "🕵️ «Шерлок». Если информация существует — я её найду.\n\n"
    "Отправьте данные или фото."
)

@router.message(F.text == "/start")
@router.message(F.text == "📂 Показать меню")
async def start_handler(message: Message):
    user = get_user(message.from_user.id)
    if message.from_user.id == OWNER_ID:
        user["role"] = "owner"

    await message.answer(START_TEXT, reply_markup=main_menu_kb)
    await message.answer("Меню ⬇️", reply_markup=bottom_kb)

@router.message(F.text == "👤 Мой профиль")
async def profile(message: Message):
    user = get_user(message.from_user.id)

    if user["role"] == "owner":
        access = "👑 Владелец"
        left = "∞"
    elif user["free"] > 0:
        access = "🎁 Партнёрский"
        left = user["free"]
    else:
        access = "💳 Стандартный"
        left = user["balance"]

    await message.answer(
        f"Ваш ID: {message.from_user.id}\n"
        f"Тип доступа: {access}\n"
        f"Доступно поисков: {left}"
    )

# ========= SEARCH =========
@router.message(F.text == "🔍 Поиск по неполным данным")
async def start_search(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(SearchState.fill_form)

    await message.answer(
        "Заполните любые поля:",
        reply_markup=search_keyboard({})
    )

@router.message(SearchState.fill_form, F.text.in_(FIELDS_MAP))
async def ask_value(message: Message, state: FSMContext):
    await state.update_data(last=FIELDS_MAP[message.text])
    await state.set_state(SearchState.waiting_value)
    await message.answer("Введите значение:", reply_markup=cancel_kb)

@router.message(SearchState.waiting_value, F.text)
async def save_value(message: Message, state: FSMContext):
    data = await state.get_data()
    form = data.get("form", {})
    form[data["last"]] = message.text

    await state.update_data(form=form)
    await state.set_state(SearchState.fill_form)

    await message.answer("Сохранено.", reply_markup=search_keyboard(form))

@router.message(SearchState.fill_form, F.text == "🔄 Сбросить")
async def reset(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(SearchState.fill_form)
    await message.answer("Форма очищена.", reply_markup=search_keyboard({}))

@router.message(SearchState.fill_form, F.text == "🔍 Искать")
async def run_search(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if not can_search(user):
        await message.answer("❌ Недостаточно запросов", reply_markup=payment_kb)
        return

    data = await state.get_data()
    form = data.get("form", {})
    results = mock_search(form)

    text = "🔎 Результаты:\n\n"
    for r in results:
        text += f"🔹 {r['type']}:\n• {r['value']} ({r['confidence']}%)\n\n"

    await message.answer(text, reply_markup=bottom_kb)

# ========= PAYMENTS =========
@router.message(F.text == "💰 Пополнить баланс")
async def topup(message: Message):
    await message.answer("Выберите способ:", reply_markup=payment_kb)

@router.message(F.text == "💳 CryptoBot")
async def pay(message: Message):
    user = get_user(message.from_user.id)
    user["balance"] += 5
    await message.answer("✅ Начислено 5 запросов", reply_markup=main_menu_kb)

# ========= ADMIN =========
@router.message(F.text.startswith("/grant"))
async def grant(message: Message):
    if message.from_user.id != OWNER_ID:
        return

    _, uid, amount = message.text.split()
    u = get_user(int(uid))
    u["role"] = "whitelist"
    u["free"] += int(amount)

    await message.answer(f"Выдано {amount} запросов пользователю {uid}")

# =====================
# APP
# =====================
async def main():
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
