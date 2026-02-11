import asyncio
import os
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery, LabeledPrice, PreCheckoutQuery
)
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime

# ---------------- CONFIG ----------------

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден")

STARS_PROVIDER_TOKEN = os.getenv("STARS_PROVIDER_TOKEN")

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

# ---------------- ДАННЫЕ ----------------

languages_flags = [
    ("🇷🇺 Русский", "ru"),
    ("🇬🇧 English", "en"),
]

STARS_PACKAGES = [
    {"searches": 1, "stars": 20},
    {"searches": 5, "stars": 100},
    {"searches": 10, "stars": 200},
]

CRYPTO_PACKAGES = {
    "USDT": [2, 5, 10],
    "TON": [0.5, 2, 5]
}

# ---------------- КНОПКИ ----------------

def bottom_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📂 Меню"),
                   KeyboardButton(text="👤 Профиль")]],
        resize_keyboard=True
    )

def profile_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💰 Пополнить", callback_data="top_up")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start")]
        ]
    )

# ---------------- ROUTER ----------------

router = Router()

# ---------------- START ----------------

@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.set_state(SearchState.language_selection)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"lang_{code}")]
            for name, code in languages_flags
        ]
    )

    await message.answer(
        "Выберите язык / Choose language:",
        reply_markup=kb
    )

async def show_start_content(message: Message, state: FSMContext):
    await state.set_state(SearchState.form)

    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    await state.update_data(
        balance=0,
        search_count=0,
        registration_date=now
    )

    await message.answer(
        "🕵️ Добро пожаловать в систему поиска.\n\n"
        "Выберите действие ниже 👇",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Начать поиск",
                                      callback_data="start_search")],
                [InlineKeyboardButton(text="👤 Мой профиль",
                                      callback_data="profile")]
            ]
        )
    )

    # ВАЖНО: теперь есть текст!
    await message.answer(
        "Главное меню:",
        reply_markup=bottom_keyboard()
    )

# ---------------- CALLBACK ----------------

@router.callback_query()
async def callbacks(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    fsm_data = await state.get_data()

    # --- Выбор языка ---
    if data.startswith("lang_"):
        await state.update_data(language=data.split("_")[1])
        await callback.message.delete()
        await show_start_content(callback.message, state)
        await callback.answer()
        return

    # --- Назад ---
    if data == "back_to_start":
        await callback.message.delete()
        await show_start_content(callback.message, state)
        await callback.answer()
        return

    # --- Профиль ---
    if data == "profile":
        text = (
            f"Ваш ID: {callback.from_user.id}\n\n"
            f"Баланс: ${fsm_data.get('balance', 0)}\n"
            f"Поисков доступно: {fsm_data.get('search_count', 0)}\n"
            f"Дата регистрации: {fsm_data.get('registration_date','—')}"
        )

        await callback.message.edit_text(
            text,
            reply_markup=profile_keyboard()
        )
        await callback.answer()
        return

    # --- Пополнение ---
    if data == "top_up":
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⭐ Telegram Stars",
                                      callback_data="pay_stars")],
                [InlineKeyboardButton(text="💰 Криптовалюта",
                                      callback_data="pay_crypto")],
                [InlineKeyboardButton(text="⬅️ Назад",
                                      callback_data="profile")]
            ]
        )

        await callback.message.edit_text(
            "Выберите способ оплаты:",
            reply_markup=kb
        )
        await callback.answer()
        return

    # --- Stars ---
    if data == "pay_stars":
        keyboard = [
            [InlineKeyboardButton(
                text=f"{p['searches']} поисков — {p['stars']} ⭐",
                callback_data=f"buy_stars:{i}"
            )]
            for i, p in enumerate(STARS_PACKAGES)
        ]

        await callback.message.edit_text(
            "Выберите пакет:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        await callback.answer()
        return

    if data.startswith("buy_stars:") and STARS_PROVIDER_TOKEN:
        idx = int(data.split(":")[1])
        p = STARS_PACKAGES[idx]

        prices = [
            LabeledPrice(
                label=f"{p['searches']} поисков",
                amount=p['stars']
            )
        ]

        await callback.message.answer_invoice(
            title="Пополнение",
            description="Покупка поисков",
            payload=f"stars:{idx}",
            provider_token=STARS_PROVIDER_TOKEN,
            currency="XTR",
            prices=prices
        )

        await callback.answer()
        return

    # --- Crypto ---
    if data == "pay_crypto":
        keyboard = [
            [InlineKeyboardButton(text=c,
                                  callback_data=f"crypto_{c}")]
            for c in CRYPTO_PACKAGES
        ]

        await callback.message.edit_text(
            "Выберите криптовалюту:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        await callback.answer()
        return

    if data.startswith("crypto_"):
        crypto = data.split("_")[1]
        wallet = CRYPTO_WALLETS[crypto]

        await callback.message.answer(
            f"Оплатите на кошелек:\n\n{wallet}\n\n"
            f"После оплаты запросы начисляются вручную."
        )

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
