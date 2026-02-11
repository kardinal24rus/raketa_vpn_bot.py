import asyncio
import os
from aiogram import Bot, Dispatcher, Router
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, LabeledPrice
)
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime

# ------------------ CONFIG ------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден")

STARS_PROVIDER_TOKEN = os.getenv("STARS_PROVIDER_TOKEN")  # Для Telegram Stars
CRYPTO_WALLETS = {
    "USDT": "UQAKrbQwdQWKzSrVPU-KwcJvF6SkZUBPQHzEJtABznMvoA7X",
    "TON": "UQA9h8H460r7ESOSuzHYgKqYfD9sSex6uet2XzVYq2g-2iFN"
}

# ------------------ FSM ------------------
class SearchState(StatesGroup):
    language_selection = State()
    form = State()
    current_input = State()
    choose_payment = State()

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

# ------------------ TARIFFS ------------------
STARS_PACKAGES = [
    {"searches": 1, "stars": 20},
    {"searches": 5, "stars": 100},
    {"searches": 10, "stars": 200},
]

CRYPTO_PACKAGES = {
    "USDT": [2,5,10],
    "TON": [0.5,2,5]
}

# ------------------ KEYBOARDS ------------------
def bottom_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📂 Показать меню"), KeyboardButton(text="👤 Выбрать пользователя")]],
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

# ------------------ ROUTER ------------------
router = Router()

# ------------------ START ------------------
@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    data = await state.get_data()
    if "language" not in data:
        await state.set_state(SearchState.language_selection)
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=f[0], callback_data=f"lang_{f[1]}") for f in languages_flags]]
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
    
    await message.answer(
        "🕵️ Пример профиля...",
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

# ------------------ CALLBACK HANDLER ------------------
@router.callback_query(lambda c: True)
async def callback_handler(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    fsm_data = await state.get_data()
    lang = fsm_data.get("language","ru")
    t = translations[lang]

    # ---------- Выбор языка ----------
    if data.startswith("lang_"):
        await state.update_data(language=data.replace("lang_",""))
        await callback.message.delete()
        await show_start_content(callback.message, state)
        await callback.answer()
        return

    # ---------- Поиск по неполным данным ----------
    if data == "partial_search":
        await state.set_state(SearchState.form)
        await callback.message.delete()
        await callback.message.answer(t["partial_search"], reply_markup=get_search_form_keyboard(fsm_data, lang=lang))
        await callback.answer()
        return

    # ---------- Ввод поля ----------
    if data.startswith("input_"):
        field = data.replace("input_","")
        await state.set_state(SearchState.current_input)
        await state.update_data(current_field=field)
        await callback.message.answer(
            t["input_prompt"].format(field=t.get(field,field)),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t["cancel"], callback_data="cancel_input")]])
        )
        await callback.answer()
        return

    if data == "cancel_input":
        await state.set_state(SearchState.form)
        fsm_data = await state.get_data()
        await callback.message.delete()
        await callback.message.answer("Форма поиска:", reply_markup=get_search_form_keyboard(fsm_data, lang=lang))
        await callback.answer("Ввод отменён ✅")
        return

    # ---------- Назад ----------
    if data == "back_to_start" or data == "back":
        await callback.message.delete()
        await show_start_content(callback.message, state)
        await callback.answer()
        return

    # ---------- Сбросить форму ----------
    if data == "reset_form":
        await state.update_data({k:"" for k in ["surname","name","patronymic","day","month","year","age_from","age","age_to","birthplace","country"]})
        await state.set_state(SearchState.form)
        await callback.message.delete()
        await callback.message.answer(t["form_cleared"], reply_markup=get_search_form_keyboard({}, lang=lang))
        await callback.answer()
        return

    # ---------- Искать ----------
    if data == "search_data":
        search_preview = "\n".join([f"{k}: {v}" for k,v in fsm_data.items() if v and k!="current_field"])
        search_preview = search_preview or "⚠️ Пока ничего не введено"
        await callback.message.answer(f"{t['search_preview']}\n{search_preview}")
        await callback.answer()
        return

    # ---------- Профиль ----------
    if data == "profile":
        profile_text = (
            f"Ваш ID: {callback.from_user.id}\n\n"
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

    # ---------- Пополнение ----------
    if data == "top_up":
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⭐ Telegram Stars", callback_data="pay_stars")],
                [InlineKeyboardButton(text="💰 Криптовалюта", callback_data="pay_crypto")],
                [InlineKeyboardButton(text=t["back"], callback_data="profile")]
            ]
        )
        await callback.message.edit_text(t["payment_prompt"], reply_markup=kb)
        await callback.answer()
        return

    # ----- Stars -----
    if data == "pay_stars":
        keyboard = [[InlineKeyboardButton(text=f"{p['searches']} поисков — {p['stars']} ⭐", callback_data=f"buy_stars:{i}")] for i,p in enumerate(STARS_PACKAGES)]
        keyboard.append([InlineKeyboardButton(text=t["back"], callback_data="top_up")])
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

    # ----- Crypto -----
    if data == "pay_crypto":
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=c, callback_data=f"crypto_{c}")] for c in CRYPTO_PACKAGES]
        )
        kb.inline_keyboard.append([InlineKeyboardButton(text=t["back"], callback_data="top_up")])
        await callback.message.edit_text("Выберите криптовалюту:", reply_markup=kb)
        await callback.answer()
        return

    if data.startswith("crypto_"):
        crypto = data.split("_")[1]
        wallet = CRYPTO_WALLETS[crypto]
        await callback.message.answer(
            f"💰 Оплата {crypto}\nОтправьте сумму на этот кошелек:\n{wallet}\n\n"
            f"После оплаты ваши поиски будут начислены автоматически."
        )
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
