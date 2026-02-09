# bot_main.py
import asyncio, os, hashlib
from collections import defaultdict
from aiogram import Bot, Dispatcher, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --------------------------
# Настройки
# --------------------------
API_TOKEN = os.environ.get("API_TOKEN", "ВАШ_ТОКЕН_BOT")  # токен из .env или напрямую
OWNER_ID = int(os.environ.get("OWNER_ID", 7014418816))

# --------------------------
# Инициализация бота
# --------------------------
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --------------------------
# "База данных" (упрощенно)
# --------------------------
USERS_DB = {}
SEARCH_LOGS = []

def get_user(user_id):
    return USERS_DB.get(user_id)

def get_or_create_user(user_id):
    if user_id not in USERS_DB:
        USERS_DB[user_id] = {
            "telegram_id": user_id,
            "search_credits": 0,
            "free_credits": 0,
            "is_owner": user_id == OWNER_ID,
        }
    return USERS_DB[user_id]

def can_search(user):
    return user["is_owner"] or user["free_credits"] > 0 or user["search_credits"] > 0

def consume_search(user):
    if user["is_owner"]:
        return
    if user["free_credits"] > 0:
        user["free_credits"] -= 1
    else:
        user["search_credits"] -= 1

def hash_query(data):
    text = str(sorted(data.items()))
    return hashlib.sha256(text.encode()).hexdigest()

# --------------------------
# FSM для поиска
# --------------------------
class SearchForm(StatesGroup):
    menu = State()
    input = State()

FORM_FIELDS = {
    "last_name": "Фамилия",
    "first_name": "Имя",
    "middle_name": "Отчество",
    "day": "День",
    "month": "Месяц",
    "year": "Год",
    "age_from": "Возраст от",
    "age": "Возраст",
    "age_to": "Возраст до",
    "birthplace": "Место рождения",
    "country": "Страна",
}

def build_search_keyboard(data: dict):
    buttons = []
    for key, title in FORM_FIELDS.items():
        if key in data:
            buttons.append(InlineKeyboardButton(f"✅ {data[key]}", callback_data=f"edit:{key}"))
        else:
            buttons.append(InlineKeyboardButton(title, callback_data=f"add:{key}"))
    buttons.extend([
        InlineKeyboardButton("♻️ Сбросить", callback_data="reset"),
        InlineKeyboardButton("🔍 Искать", callback_data="search")
    ])
    return InlineKeyboardMarkup(inline_keyboard=[buttons[i:i+2] for i in range(0, len(buttons), 2)])

# --------------------------
# Главное меню
# --------------------------
@dp.message(F.text == "/start")
async def cmd_start(message: types.Message, state: FSMContext):
    get_or_create_user(message.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Поиск по неполным данным", callback_data="search_partial")],
        [InlineKeyboardButton("Мой профиль", callback_data="my_profile")],
        [InlineKeyboardButton("Мои боты", callback_data="my_bots")],
        [InlineKeyboardButton("Партнёрская программа", callback_data="partner_program")],
    ])
    await message.answer("🕵️ Добро пожаловать!", reply_markup=kb)

# --------------------------
# Поиск по неполным данным
# --------------------------
@dp.callback_query(F.data == "search_partial")
async def start_search(call: types.CallbackQuery, state: FSMContext):
    user = get_or_create_user(call.from_user.id)
    if not can_search(user):
        await call.message.answer("❌ Недостаточно запросов. Пополните баланс.")
        return
    await state.clear()
    await state.set_state(SearchForm.menu)
    await call.message.answer("Вы можете указать любое количество данных...", reply_markup=build_search_keyboard({}))

@dp.callback_query(F.data.startswith("add:"))
async def ask_input(call: types.CallbackQuery, state: FSMContext):
    field = call.data.split(":")[1]
    await state.update_data(current_field=field)
    await state.set_state(SearchForm.input)
    await call.message.answer(
        f"Введите {FORM_FIELDS[field].lower()}:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
        ])
    )

@dp.message(SearchForm.input)
async def save_input(message: types.Message, state: FSMContext):
    data = await state.get_data()
    field = data["current_field"]
    await state.update_data(**{field: message.text})
    await state.set_state(SearchForm.menu)
    form_data = await state.get_data()
    form_data.pop("current_field", None)
    await message.answer("Данные обновлены:", reply_markup=build_search_keyboard(form_data))

@dp.callback_query(F.data == "reset")
async def reset_form(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(SearchForm.menu)
    await call.message.edit_reply_markup(reply_markup=build_search_keyboard({}))

# --------------------------
# Поиск и вывод результатов
# --------------------------
def run_osint_search(form_data):
    # Заглушка для реального поиска
    results = []
    if form_data.get("last_name"):
        results.append({"category": "identity", "value": form_data["last_name"], "source": "Публичный профиль"})
    if form_data.get("birthplace"):
        results.append({"category": "
