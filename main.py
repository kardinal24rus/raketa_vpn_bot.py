import asyncio
import os
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from datetime import datetime

# ------------------ CONFIG ------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден в переменных окружения")

# ------------------ FSM ------------------
class SearchState(StatesGroup):
    language_selection = State()
    form = State()
    current_input = State()

class PaymentState(StatesGroup):
    choose_method = State()
    choose_package = State()

class CryptoPaymentState(StatesGroup):
    choose_package = State()
    confirm_payment = State()

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
    }
}

languages_flags = [
    ("🇷🇺 Русский", "ru"),
]

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

# ------------------ PRICES ------------------
STARS_PACKAGES = {
    "p1": {"searches": 1, "stars": 20},
    "p5": {"searches": 5, "stars": 100},
    "p10": {"searches": 10, "stars": 200},
    "p15": {"searches": 15, "stars": 300},
    "p20": {"searches": 20, "stars": 400},
    "p100": {"searches": 100, "stars": 1490},
}

CRYPTO_USDT = [2, 4, 6, 9, 30]  # USDT
CRYPTO_TON = [0.3, 1.5, 3.5, 5, 7, 25]  # TON

# ------------------ ROUTER ------------------
router = Router()

# ------------------ START ------------------
@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    data = await state.get_data()
    if "language" not in data:
        await state.set_state(SearchState.language_selection)
        await message.answer(translations["ru"]["language_prompt"], reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=languages_flags[0][0], callback_data=f"lang_{languages_flags[0][1]}")]]
        ))
    else:
        await show_start_content(message, state)

async def show_start_content(message: Message, state: FSMContext):
    await state.set_state(SearchState.form)
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    await state.update_data(balance=0, search_count=0, referral_balance=0, registration_date=now, agent_duration="6 мес., 16 дн.")
    await message.answer("Добро пожаловать! Выберите действие:", reply_markup=profile_keyboard())
    await message.answer(reply_markup=bottom_keyboard())

# ------------------ CALLBACK ------------------
@router.callback_query(lambda c: True)
async def callback_handler(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    fsm_data = await state.get_data()

    # ---------- Выбор языка ----------
    if data.startswith("lang_"):
        await state.update_data(language=data.replace("lang_", ""))
        await callback.message.delete()
        await show_start_content(callback.message, state)
        await callback.answer()
        return

    # ---------- ПОПОЛНИТЬ ----------
    if data == "top_up":
        keyboard = [
            [InlineKeyboardButton(text="⭐ Звёзды", callback_data="pay_stars")],
            [InlineKeyboardButton(text="💎 Крипта", callback_data="pay_crypto")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="profile")]
        ]
        await state.set_state(PaymentState.choose_method)
        await callback.message.edit_text("💰 Выберите способ оплаты:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
        await callback.answer()
        return

    # ---------- ЗВЁЗДЫ ----------
    if data == "pay_stars":
        keyboard = [[InlineKeyboardButton(text=f"{p['searches']} поисков — {p['stars']} ⭐", callback_data=f"buy_stars:{key}")] for key,p in STARS_PACKAGES.items()]
        keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="top_up")])
        await callback.message.edit_text("Выберите пакет для покупки:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
        await callback.answer()
        return

    if data.startswith("buy_stars:"):
        key = data.split(":")[1]
        searches = STARS_PACKAGES[key]["searches"]
        current = fsm_data.get("search_count",0)
        await state.update_data(search_count=current + searches)
        await callback.message.edit_text(f"✅ Начислено {searches} поисков!\n📊 Всего: {current + searches}")
        await callback.answer()
        return

    # ---------- КРИПТА ----------
    if data == "pay_crypto":
        keyboard = [
            [InlineKeyboardButton(text="💵 USDT", callback_data="crypto_usdt")],
            [InlineKeyboardButton(text="🌐 TON", callback_data="crypto_ton")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="top_up")]
        ]
        await state.set_state(CryptoPaymentState.choose_package)
        await callback.message.edit_text("💎 Оплата криптой:\nВыберите валюту:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
        await callback.answer()
        return

    if data == "crypto_usdt":
        keyboard = [[InlineKeyboardButton(text=f"{p} USDT", callback_data=f"crypto_usdt_{p}")] for p in CRYPTO_USDT]
        keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="pay_crypto")])
        await state.set_state(CryptoPaymentState.confirm_payment)
        await callback.message.edit_text("💵 Оплата USDT:\nВыберите пакет и отправьте сумму на кошелек:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
        await callback.answer()
        return

    if data == "crypto_ton":
        keyboard = [[InlineKeyboardButton(text=f"{p} TON", callback_data=f"crypto_ton_{p}")] for p in CRYPTO_TON]
        keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="pay_crypto")])
        await state.set_state(CryptoPaymentState.confirm_payment)
        await callback.message.edit_text("🌐 Оплата TON:\nВыберите пакет и отправьте сумму на кошелек:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
        await callback.answer()
        return

    if data.startswith("crypto_usdt_") or data.startswith("crypto_ton_"):
        payload = data.split("_")
        currency = payload[1]
        amount = payload[2]
        if currency == "usdt":
            searches_map = {"2":1,"4":5,"6":10,"9":15,"30":100}
        else:
            searches_map = {"0.3":1,"1.5":5,"3.5":10,"5":15,"7":20,"25":100}
        searches = searches_map.get(amount,0)
        current = fsm_data.get("search_count",0)
        await state.update_data(search_count=current + searches)
        await callback.message.edit_text(f"✅ Оплата {currency.upper()} прошла!\n🔍 Начислено {searches} поисков\n📊 Всего: {current + searches}")
        await state.set_state(None)
        await callback.answer()
        return

    # ---------- ПРОФИЛЬ ----------
    if data == "profile":
        profile_text = (
            f"Ваш ID: {callback.from_user.id}\n"
            f"Доступно поисков: {fsm_data.get('search_count',0)}\n"
            f"Баланс: {fsm_data.get('balance',0)}\n"
            f"Реферальный баланс: {fsm_data.get('referral_balance',0)}\n"
            f"Дата регистрации: {fsm_data.get('registration_date','—')}\n"
            f"(Вы агент уже: {fsm_data.get('agent_duration','—')})"
        )
        await callback.message.edit_text(profile_text, reply_markup=profile_keyboard())
        await callback.answer()
        return

# ------------------ MAIN ------------------
async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
