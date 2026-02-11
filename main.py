import asyncio
import os
from aiogram import Bot, Dispatcher, Router
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery,
    LabeledPrice, PreCheckoutQuery
)
from aiogram.filters import CommandStart, Text
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime

# ------------------ CONFIG ------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден в переменных окружения")

CRYPTO_WALLETS = {
    "USDT": "ВАШ_USDT_АДРЕС",
    "TON": "ВАШ_TON_АДРЕС"
}

STARS_PROVIDER_TOKEN = os.getenv("STARS_PROVIDER_TOKEN")  # Для Telegram Stars

# ------------------ FSM ------------------
class SearchState(StatesGroup):
    language_selection = State()
    form = State()
    current_input = State()
    choose_payment = State()
    choose_package = State()

# ------------------ TRANSLATIONS ------------------
translations = {
    "ru": {
        "surname": "Фамилия", "name": "Имя", "patronymic": "Отчество",
        "day": "День", "month": "Месяц", "year": "Год",
        "age_from": "Возраст от", "age": "Возраст", "age_to": "Возраст до",
        "birthplace": "Место рождения", "country": "Страна",
        "back": "⬅️ Назад", "reset": "🗑 Сбросить", "search": "🔍 Искать",
        "cancel": "Отмена",
        "input_prompt": "Введите {field}:",
        "form_cleared": "Форма очищена:",
        "search_preview": "🔍 Предварительный просмотр поиска:",
        "partial_search": "Вы можете указать любое количество данных.\nЧем больше данных — тем точнее результат.\n\nФорма поиска готова 👇",
        "language_prompt": "Выберите язык / Choose language:",
        "payment_prompt": "💰 Выберите способ оплаты:",
        "package_prompt": "Выберите пакет поисков:",
    }
}

languages_flags = [
    ("🇷🇺 Русский", "ru"),
    ("🇬🇧 English", "en"),
]

# ------------------ ТАРИФЫ ------------------
STARS_PACKAGES = [
    {"searches": 1, "stars": 20},
    {"searches": 5, "stars": 100},
    {"searches": 10, "stars": 200},
    {"searches": 15, "stars": 300},
    {"searches": 20, "stars": 400},
    {"searches": 100, "stars": 1490},
]

CRYPTO_PACKAGES = {
    "USDT": [2,4,6,9,30],  # фиксированные суммы
    "TON": [0.3,1.5,3.5,5,7,25]
}

# ------------------ KEYBOARDS ------------------
def bottom_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📂 Показать меню"), KeyboardButton(text="👤 Выбрать пользователя")]],
        resize_keyboard=True
    )

def get_search_form_keyboard(data: dict):
    def val_or_default(key):
        return f"{data[key]} ✅" if key in data and data[key] else translations["ru"].get(key, key)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=val_or_default("surname"), callback_data="input_surname"),
                InlineKeyboardButton(text=val_or_default("name"), callback_data="input_name"),
                InlineKeyboardButton(text=val_or_default("patronymic"), callback_data="input_patronymic"),
            ],
            [
                InlineKeyboardButton(text=val_or_default("day"), callback_data="input_day"),
                InlineKeyboardButton(text=val_or_default("month"), callback_data="input_month"),
                InlineKeyboardButton(text=val_or_default("year"), callback_data="input_year"),
            ],
            [
                InlineKeyboardButton(text=val_or_default("age_from"), callback_data="input_age_from"),
                InlineKeyboardButton(text=val_or_default("age"), callback_data="input_age"),
                InlineKeyboardButton(text=val_or_default("age_to"), callback_data="input_age_to"),
            ],
            [
                InlineKeyboardButton(text=val_or_default("birthplace"), callback_data="input_birthplace")
            ],
            [
                InlineKeyboardButton(text=val_or_default("country"), callback_data="input_country")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start"),
                InlineKeyboardButton(text="🗑 Сбросить", callback_data="reset_form"),
                InlineKeyboardButton(text="🔍 Искать", callback_data="search_data")
            ]
        ]
    )

def profile_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💰 Пополнить", callback_data="top_up"),
                InlineKeyboardButton(text="🔍 Купить запросы", callback_data="buy_requests")
            ],
            [
                InlineKeyboardButton(text="🚫 Скрытие данных из поиска", callback_data="hide_data")
            ],
            [
                InlineKeyboardButton(text="👁 Отслеживание поисков", callback_data="tracking")
            ],
            [
                InlineKeyboardButton(text="🎩 Связаться с нами", callback_data="contact")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back"),
                InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
                InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh")
            ]
        ]
    )

# ------------------ ROUTER ------------------
router = Router()

# ------------------ START ------------------
@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    data = await state.get_data()
    if "language" not in data:
        await state.set_state(SearchState.language_selection)
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=f[0], callback_data=f"lang_{f[1]}")] for f in languages_flags]
        )
        await message.answer(translations["ru"]["language_prompt"], reply_markup=kb)
    else:
        await show_start_content(message, state)

async def show_start_content(message: Message, state: FSMContext):
    await state.set_state(SearchState.form)
    now = datetime.now().strftime
