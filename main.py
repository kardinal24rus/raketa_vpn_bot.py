import asyncio
import os
from aiogram import Bot, Dispatcher, Router
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery, LabeledPrice
)
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден")
STARS_PROVIDER_TOKEN = os.getenv("STARS_PROVIDER_TOKEN")  # Stars токен
CRYPTO_WALLETS = {
    "USDT": "ВАШ_USDT_АДРЕС",
    "TON": "ВАШ_TON_АДРЕС"
}

# ---------------- FSM ----------------
class SearchState(StatesGroup):
    language_selection = State()
    form = State()
    current_input = State()
    choose_payment = State()

# ---------------- TRANSLATIONS ----------------
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
        "package_prompt": "Выберите пакет поисков:"
    },
    "en": {
        "surname": "Surname", "name": "Name", "patronymic": "Patronymic",
        "day": "Day", "month": "Month", "year": "Year",
        "age_from": "Age from", "age": "Age", "age_to": "Age to",
        "birthplace": "Birthplace", "country": "Country",
        "back": "⬅️ Back", "reset": "🗑 Reset", "search": "🔍 Search",
        "cancel": "Cancel",
        "input_prompt": "Enter {field}:",
        "form_cleared": "Form cleared:",
        "search_preview": "🔍 Search preview:",
        "partial_search": "You can provide any number of fields.\nThe more data — the more accurate the results.\n\nSearch form ready 👇",
        "language_prompt": "Select language / Выберите язык:",
        "payment_prompt": "💰 Choose payment method:",
        "package_prompt": "Select search package:"
    }
}

languages_flags = [
    ("🇷🇺 Русский", "ru"),
    ("🇬🇧 English", "en")
]

# ---------------- PACKAGES ----------------
STARS_PACKAGES = [
    {"searches": 1, "stars": 20},
    {"searches": 5, "stars": 100},
    {"searches": 10, "stars": 200},
]
CRYPTO_PACKAGES = {
    "USDT": [2, 5, 10],
    "TON": [0.5, 2, 5]
}

# ---------------- KEYBOARDS ----------------
def bottom_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📂 Показать меню"),
                   KeyboardButton(text="👤 Выбрать пользователя")]],
        resize_keyboard=True
    )

def get_search_form_keyboard(data: dict, lang="ru"):
    t = translations[lang]
    def val_or_default(key):
        return f"{data[key]} ✅" if key in data and data[key] else t.get(key, key)
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
                InlineKeyboardButton(text=t["back"], callback_data="back_to_start"),
                InlineKeyboardButton(text=t["reset"], callback_data="reset_form"),
                InlineKeyboardButton(text=t["search"], callback_data="search_data")
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

# ---------------- ROUTER ----------------
router = Router()

# ---------------- START ----------------
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
    data = await state.get_data()
    lang = data.get("language","ru")
    await state.set_state(SearchState.form)
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    await state.update_data(balance=0, search_count=0, referral_balance=0, registration_date=now, agent_duration="6 мес., 16 дн.")

    # --- Основное сообщение с профилем ---
    await message.answer(
        "🕵️ Личность:\n"
        "Навальный Алексей Анатольевич 04.06.1976 - ФИО\n\n"
        "📲 Контакты:\n79999688666 – номер телефона\n79999688666@mail.ru – email\n\n"
        "🚘 Транспорт:\nВ395ОК199 – номер автомобиля\nXTA211440C5106924 – VIN автомобиля\n\n"
        "💬 Социальные сети:\nvk.com/sherlock – Вконтакте\ntiktok.com/@sherlock – Tiktok\ninstagram.com/sherlock – Instagram\nok.ru/profile/58460 – Одноклассники\n\n"
        "📟 Telegram:\n@sherlock, tg123456 – логин или ID\n\n"
        "📄 Документы:\n/vu 1234567890 – водительские права\n/passport 1234567890 – паспорт\n/snils 12345678901 – СНИЛС\n/inn 123456789012 – ИНН\n\n"
        "🌐 Онлайн-следы:\n/tag хирург москва – поиск по телефонным книгам\nsherlock.com или 1.1.1.1 – домен или IP\n\n"
        "🏚 Недвижимость:\n/adr Москва, Островитянова, 9к4, 94\n77:01:0004042:6987 - кадастровый номер\n\n"
        "🏢 Юридическое лицо:\n/inn 2540214547 – ИНН\n1107449004464 – ОГРН или ОГРНИП\n\n"
        "📸 Отправьте лицо человека, чтобы попробовать найти его.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Поиск по неполным данным", callback_data="partial_search")],
                [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile"),
                 InlineKeyboardButton(text="🤖 Мои боты", callback_data="my_bots")],
                [InlineKeyboardButton(text="🤝 Партнёрская программа", callback_data="partner_program")]
            ]
        )
    )
    await message.answer(reply_markup=bottom_keyboard())

# ---------------- CALLBACK ----------------
@router.callback_query(lambda c: True)
async def callback_handler(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    fsm_data = await state.get_data()
    lang = fsm_data.get("language","ru")
    t = translations[lang]

    # --- Выбор языка ---
    if data.startswith("lang_"):
        await state.update_data(language=data.replace("lang_", ""))
        await callback.message.delete()
        await show_start_content(callback.message, state)
        await callback.answer()
        return

    # --- Профиль ---
    if data == "profile":
        profile_text = (
            f"Ваш ID: {callback.from_user.id}\n"
            f"Доступно поисков: {fsm_data.get('search_count',0)}\n"
            f"Ваш баланс: ${fsm_data.get('balance',0):.2f}\n"
            f"Реферальный баланс: ${fsm_data.get('referral_balance',0):.2f}\n"
            f"Дата регистрации: {fsm_data.get('registration_date','—')}\n"
            f"(Вы агент уже: {fsm_data.get('agent_duration','—')})"
        )
        await callback.message.delete()
        await callback.message.answer(profile_text, reply_markup=profile_keyboard())
        await callback.answer()
        return

    # --- Пополнение ---
    if data == "top_up":
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⭐ Telegram Stars", callback_data="pay_stars")],
                [InlineKeyboardButton(text="💰 Криптовалюта", callback_data="pay_crypto")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="profile")]
            ]
        )
        await callback.message.edit_text(t["payment_prompt"], reply_markup=kb)
        await callback.answer()
        return

    # --- Stars ---
    if data == "pay_stars":
        keyboard = [[InlineKeyboardButton(text=f"{p['searches']} поисков — {p['stars']} ⭐",
                                          callback_data=f"buy_stars:{i}")] for i,p in enumerate(STARS_PACKAGES)]
        keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="top_up")])
        await callback.message.edit_text(t["package_prompt"], reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
        await callback.answer()
        return

    if data.startswith("buy_stars:") and STARS_PROVIDER_TOKEN:
        idx = int(data.split(":")[1])
        p = STARS_PACKAGES[idx]
        prices = [LabeledPrice(label=f"{p['searches']} поисков", amount=p["stars"])]
        await callback.message.answer_invoice(
            title="Пополнение поисков",
            description=f"Начисление {p['searches']} поисков",
            payload=f"stars:{idx}",
            provider_token=STARS_PROVIDER_TOKEN,
            currency="XTR",
            prices=prices
        )
        await callback.answer()
        return

    # --- Crypto ---
    if data == "pay_crypto":
        keyboard = [[InlineKeyboardButton(text=c, callback_data=f"crypto_{c}")] for c in CRYPTO_PACKAGES]
        keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="top_up")])
        await callback.message.edit_text("Выберите криптовалюту:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
        await callback.answer()
        return

    if data.startswith("crypto_"):
        crypto = data.split("_")[1]
        wallet = CRYPTO_WALLETS[crypto]
        await callback.message.answer(f"Оплатите на кошелек:\n{wallet}\n\nПосле оплаты ваши поиски будут начислены автоматически.")
        await callback.answer()
        return

# ---------------- MAIN ----------------
async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
