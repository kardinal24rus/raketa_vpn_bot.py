import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from collections import defaultdict
import os

# =====================
# Настройки
# =====================
API_TOKEN = os.environ.get("API_TOKEN")  # Установи переменную окружения на Runway
OWNER_ID = 7014418816  # твой Telegram ID

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# =====================
# Модель данных (упрощённо)
# =====================
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

# =====================
# FSM для поиска
# =====================
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
    # Разбиваем кнопки по 2 в ряд
    return InlineKeyboardMarkup(inline_keyboard=[buttons[i:i+2] for i in range(0, len(buttons), 2)])

# =====================
# Старт / Главное меню
# =====================
@dp.message(F.text == "/start")
async def cmd_start(message: types.Message, state: FSMContext):
    user = get_or_create_user(message.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Поиск по неполным данным", callback_data="search_partial")],
        [InlineKeyboardButton("Мой профиль", callback_data="my_profile")],
        [InlineKeyboardButton("Мои боты", callback_data="my_bots")],
        [InlineKeyboardButton("Партнёрская программа", callback_data="partner_program")],
    ])
    await message.answer("🕵️ Добро пожаловать!", reply_markup=kb)

# =====================
# Поиск
# =====================
@dp.callback_query(F.data == "search_partial")
async def start_search(call: types.CallbackQuery, state: FSMContext):
    user = get_or_create_user(call.from_user.id)
    if not can_search(user):
        await call.message.answer("❌ Недостаточно запросов. Пополните баланс.")
        return
    await state.clear()
    await state.set_state(SearchForm.menu)
    await call.message.answer(
        "Вы можете указать любое количество данных...",
        reply_markup=build_search_keyboard({})
    )

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

# =====================
# Поиск / вывод результатов
# =====================
def run_osint_search(form_data):
    # Заглушка для поиска
    results = []
    if form_data.get("last_name"):
        results.append({"category": "identity", "value": form_data["last_name"], "source": "Публичный профиль"})
    if form_data.get("birthplace"):
        results.append({"category": "online", "value": f"Упоминание в {form_data['birthplace']}", "source": "Новости"})
    return results

def format_results(results: list) -> str:
    grouped = defaultdict(list)
    for r in results:
        grouped[r["category"]].append(r)
    if not grouped:
        return "❌ По указанным данным ничего не найдено."
    text = "🕵️ Результаты поиска\n\n"
    CATEGORY_TITLES = {
        "identity": "🕵️ Личность",
        "contacts": "📲 Контакты",
        "socials": "💬 Социальные сети",
        "online": "🌐 Онлайн-следы",
        "photos": "📸 Фото",
    }
    for cat, items in grouped.items():
        title = CATEGORY_TITLES.get(cat, cat)
        text += f"{title}:\n"
        for item in items:
            text += f"• {item['value']}\n  ↳ источник: {item['source']}\n"
        text += "\n"
    return text

@dp.callback_query(F.data == "search")
async def perform_search(call: types.CallbackQuery, state: FSMContext):
    user = get_or_create_user(call.from_user.id)
    if not can_search(user):
        await call.message.answer("❌ Недостаточно запросов. Пополните баланс.")
        return
    form_data = await state.get_data()
    if not form_data:
        await call.message.answer("⚠️ Вы не указали ни одного параметра")
        return
    results = run_osint_search(form_data)
    text = format_results(results)
    await call.message.answer(text)
    consume_search(user)
    SEARCH_LOGS.append({"user_id": user["telegram_id"], "query": form_data})

# =====================
# Админка
# =====================
@dp.message(F.text == "/admin")
async def admin_panel(message: types.Message, state: FSMContext):
    if message.from_user.id != OWNER_ID:
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🎁 Выдать бесплатные запросы", callback_data="admin_grant")],
        [InlineKeyboardButton("💳 Просмотр баланса", callback_data="admin_balance")],
        [InlineKeyboardButton("📊 Логи поиска", callback_data="admin_logs")],
    ])
    await message.answer("🛠 Админ-панель", reply_markup=kb)

# ---- Выдача бесплатных запросов ----
@dp.callback_query(F.data == "admin_grant")
async def admin_grant(call: types.CallbackQuery, state: FSMContext):
    await state.set_state("grant_select_user")
    await call.message.answer("Введите Telegram ID пользователя:")

@dp.message(F.text.regexp(r"^\d+$"), state="grant_select_user")
async def grant_ask_amount(message: types.Message, state: FSMContext):
    await state.update_data(user_id=int(message.text))
    await state.set_state("grant_enter_amount")
    await message.answer("Сколько бесплатных запросов выдать?")

@dp.message(F.text.regexp(r"^\d+$"), state="grant_enter_amount")
async def grant_save(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data["user_id"]
    amount = int(message.text)
    user = get_or_create_user(user_id)
    user["free_credits"] += amount
    await message.answer(f"✅ Пользователю {user_id} выдано {amount} бесплатных запросов")
    try:
        await bot.send_message(user_id, f"🎁 Вам выдано {amount} бесплатных запросов администратором")
    except:
        pass
    await state.clear()

# ---- Просмотр баланса ----
@dp.callback_query(F.data == "admin_balance")
async def admin_balance(call: types.CallbackQuery):
    await call.message.answer("Введите Telegram ID пользователя для проверки баланса:")
    await dp.current_state(chat=call.from_user.id).set_state("admin_balance_input")

@dp.message(F.text.regexp(r"^\d+$"), state="admin_balance_input")
async def admin_balance_show(message: types.Message, state: FSMContext):
    user = get_or_create_user(int(message.text))
    await message.answer(
        f"💳 Баланс пользователя {user['telegram_id']}:\n"
        f"- Оплаченные запросы: {user['search_credits']}\n"
        f"- Бесплатные запросы: {user['free_credits']}\n"
        f"- Роль: {'OWNER' if user['is_owner'] else 'USER'}"
    )
    await state.clear()

# ---- Просмотр логов ----
@dp.callback_query(F.data == "admin_logs")
async def admin_logs(call: types.CallbackQuery):
    text = "📊 Последние поиски:\n"
    for log in SEARCH_LOGS[-10:]:
        text += f"{log['user_id']} — {log['query']}\n"
    await call.message.answer(text)

# =====================
# Запуск бота
# =====================
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    asyncio.run(dp.start_polling(bot))
