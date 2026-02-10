import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

API_TOKEN = os.getenv("API_TOKEN")  # Убедись, что переменная окружения API_TOKEN установлена

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ===== Состояния =====
class SearchStates(StatesGroup):
    waiting_for_field_input = State()
    waiting_for_search = State()

# ===== Хранилище пользователей =====
users_data = {}  # user_id: {balance, free_requests, search_data}

# ===== Главное меню =====
def main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Поиск по неполным данным", callback_data="search_partial"),
        InlineKeyboardButton(text="Мой профиль", callback_data="my_profile")
    )
    builder.row(
        InlineKeyboardButton(text="Мои боты", callback_data="my_bots"),
        InlineKeyboardButton(text="Партнёрская программа", callback_data="partner_program")
    )
    return builder.as_markup()

# ===== Языковой выбор =====
def language_menu():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang_ru"),
        InlineKeyboardButton(text="English 🇬🇧", callback_data="lang_en")
    )
    return builder.as_markup()

# ===== Кнопки поиска =====
def search_buttons(user_id):
    data = users_data.get(user_id, {}).get("search_data", {})
    fields = ["Фамилия", "Имя", "Отчество", "День", "Месяц", "Год",
              "Возраст от", "Возраст", "Возраст до", "Место рождения", "Сбросить", "Страна", "Искать"]
    builder = InlineKeyboardBuilder()
    for field in fields:
        field_key = field.lower().replace(" ", "_")
        value = data.get(field_key, field)
        builder.add(InlineKeyboardButton(text=f"{value}", callback_data=f"search_{field_key}"))
    return builder.as_markup(row_width=3)

# ===== Профиль =====
def profile_buttons():
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Пополнить", callback_data="profile_topup"),
        InlineKeyboardButton(text="Купить запросы", callback_data="profile_buy_requests"),
        InlineKeyboardButton(text="Скрытие данных", callback_data="profile_hide"),
        InlineKeyboardButton(text="Отслеживание поисков", callback_data="profile_tracking")
    )
    builder.add(
        InlineKeyboardButton(text="Связаться с нами", callback_data="profile_contact"),
        InlineKeyboardButton(text="Настройки 🔧", callback_data="profile_settings"),
        InlineKeyboardButton(text="Обновить ↻", callback_data="profile_refresh")
    )
    return builder.as_markup(row_width=2)

# ===== Прайс запросов =====
PRICE_LIST = [
    (1, "$1"),
    (10, "$5"),
    (25, "$10"),
    (65, "$20"),
    (600, "$160"),
    (10000, "$500")
]

def buy_requests_menu():
    builder = InlineKeyboardBuilder()
    for count, price in PRICE_LIST:
        builder.add(InlineKeyboardButton(text=f"{count} - {price}", callback_data=f"buy_{count}"))
    builder.add(InlineKeyboardButton(text="Назад", callback_data="profile_back"))
    return builder.as_markup(row_width=1)

# ===== Старт =====
@dp.message(Command("start"))
async def start(message: types.Message):
    # Инициализация данных пользователя
    user_id = message.from_user.id
    if user_id not in users_data:
        users_data[user_id] = {"balance": 0, "free_requests": 1, "search_data": {}}
    await message.answer("Выберите язык / Select language:", reply_markup=language_menu())

# ===== Обработка выбора языка =====
@dp.callback_query(F.data.startswith("lang_"))
async def choose_language(call: types.CallbackQuery):
    await call.message.answer("Главное меню:", reply_markup=main_menu())
    await call.answer()

# ===== Главное меню обработка =====
@dp.callback_query(F.data == "search_partial")
async def search_partial(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_id not in users_data:
        users_data[user_id] = {"balance": 0, "free_requests": 1, "search_data": {}}

    if users_data[user_id]["balance"] <= 0 and users_data[user_id]["free_requests"] <= 0:
        await call.message.answer("Пополните баланс для использования поиска.")
    else:
        users_data[user_id]["search_data"] = {}
        await call.message.answer(
            "Вы можете указать любое количество данных (все поля необязательны):",
            reply_markup=search_buttons(user_id)
        )
    await call.answer()

@dp.callback_query(F.data == "my_profile")
async def my_profile(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_id not in users_data:
        users_data[user_id] = {"balance": 0, "free_requests": 1, "search_data": {}}

    data = users_data[user_id]
    text = (f"Ваш ID: {user_id}\n"
            f"Доступно поисков: {data['free_requests']}\n"
            f"Ваш баланс: ${data['balance']}\n"
            f"Реферальный баланс: $0.00\n"
            f"Дата регистрации: 23.07.2025 17:40")
    await call.message.answer(text, reply_markup=profile_buttons())
    await call.answer()

@dp.callback_query(F.data == "my_bots")
async def my_bots(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Назад", callback_data="menu_back"))
    await call.message.answer("Раздел на завершающей стадии разработки.", reply_markup=builder.as_markup())
    await call.answer()

@dp.callback_query(F.data == "partner_program")
async def partner_program(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_id not in users_data:
        users_data[user_id] = {"balance": 0, "free_requests": 1, "search_data": {}}

    ref_link = f"https://t.me/yourbot?start={user_id}"
    text = (f"🤝 Партнёрская программа\n"
            f"Ваша реферальная ссылка: {ref_link}\n"
            f"Статистика: Баланс: $0.00, Сегодня: $0")
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Вывод средств", callback_data="withdraw"),
        InlineKeyboardButton(text="Назад", callback_data="menu_back")
    )
    await call.message.answer(text, reply_markup=builder.as_markup())
    await call.answer()

# ===== Обработка поиска =====
@dp.callback_query(F.data.startswith("search_"))
async def search_field(call: types.CallbackQuery, state: FSMContext):
    field = call.data[7:]
    user_id = call.from_user.id

    if field == "сбросить" or field == "reset":
        users_data[user_id]["search_data"] = {}
        await call.message.edit_reply_markup(reply_markup=search_buttons(user_id))
    else:
        await call.message.answer(f"Введите {field}:", reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Отмена", callback_data="cancel_input")]]))
        await state.set_state(SearchStates.waiting_for_field_input)
        await state.update_data(field=field)
    await call.answer()

@dp.callback_query(F.data == "cancel_input")
async def cancel_input(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = call.from_user.id
    await call.message.answer("Отменено.", reply_markup=search_buttons(user_id))
    await call.answer()

@dp.message(SearchStates.waiting_for_field_input)
async def input_field(message: types.Message, state: FSMContext):
    data = await state.get_data()
    field = data["field"]
    user_id = message.from_user.id
    users_data[user_id]["search_data"][field] = message.text
    await message.answer("Данные сохранены.", reply_markup=search_buttons(user_id))
    await state.clear()

# ===== Запуск бота =====
if __name__ == "__main__":
    import asyncio

    async def main():
        try:
            await dp.start_polling(bot)
        finally:
            await bot.session.close()

    asyncio.run(main())
