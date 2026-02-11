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

STARS_PROVIDER_TOKEN = os.getenv("STARS_PROVIDER_TOKEN")

CRYPTO_WALLETS = {
    "USDT": "ВАШ_USDT_АДРЕС",
    "TON": "ВАШ_TON_АДРЕС"
}

STARS_PACKAGES = [
    {"searches": 1, "stars": 20},
    {"searches": 5, "stars": 100},
    {"searches": 10, "stars": 200},
    {"searches": 15, "stars": 300},
    {"searches": 20, "stars": 400},
    {"searches": 100, "stars": 1490},
]

CRYPTO_PACKAGES = {
    "USDT": [2, 4, 6, 9, 30],
    "TON": [0.3, 1.5, 3.5, 5, 7, 25]
}

# ---------------- FSM ----------------

class SearchState(StatesGroup):
    language_selection = State()
    form = State()

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
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
            [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
        ]
    )

    await message.answer("Выберите язык / Choose language:", reply_markup=kb)

async def show_start_content(message: Message, state: FSMContext):
    await state.set_state(SearchState.form)

    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    await state.update_data(
        balance=0,
        search_count=0,
        registration_date=now
    )

    await message.answer(
        "🕵️ Добро пожаловать в систему поиска.\n\nВыберите действие 👇",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Начать поиск",
                                      callback_data="start_search")],
                [InlineKeyboardButton(text="👤 Мой профиль",
                                      callback_data="profile")]
            ]
        )
    )

    await message.answer("Главное меню:", reply_markup=bottom_keyboard())

# ---------------- CALLBACKS ----------------

@router.callback_query()
async def callbacks(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    fsm_data = await state.get_data()

    # Язык
    if data.startswith("lang_"):
        await callback.message.delete()
        await show_start_content(callback.message, state)
        await callback.answer()
        return

    # Назад в старт
    if data == "back_to_start":
        await callback.message.delete()
        await show_start_content(callback.message, state)
        await callback.answer()
        return

    # Профиль
    if data == "profile":
        text = (
            f"Ваш ID: {callback.from_user.id}\n\n"
            f"Поисков доступно: {fsm_data.get('search_count', 0)}\n"
            f"Дата регистрации: {fsm_data.get('registration_date','—')}"
        )
        await callback.message.edit_text(text, reply_markup=profile_keyboard())
        await callback.answer()
        return

    # ---------- ПОПОЛНЕНИЕ ----------

    if data == "top_up":
        await callback.message.edit_text(
            "💰 Выберите способ оплаты:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="⭐ Telegram Stars", callback_data="pay_stars")],
                    [InlineKeyboardButton(text="💰 Криптовалюта", callback_data="pay_crypto")],
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="profile")]
                ]
            )
        )
        await callback.answer()
        return

    # ---------- STARS ----------

    if data == "pay_stars":
        keyboard = [
            [InlineKeyboardButton(
                text=f"{p['searches']} поисков — {p['stars']} ⭐",
                callback_data=f"buy_stars:{i}"
            )]
            for i, p in enumerate(STARS_PACKAGES)
        ]
        keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="top_up")])

        await callback.message.edit_text(
            "Выберите пакет:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        await callback.answer()
        return

    if data.startswith("buy_stars:") and STARS_PROVIDER_TOKEN:
        idx = int(data.split(":")[1])
        p = STARS_PACKAGES[idx]

        prices = [LabeledPrice(label=f"{p['searches']} поисков",
                               amount=p['stars'])]

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

    # ---------- CRYPTO ----------

    if data == "pay_crypto":
        keyboard = [
            [InlineKeyboardButton(text=crypto,
                                  callback_data=f"crypto_{crypto}")]
            for crypto in CRYPTO_PACKAGES
        ]
        keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="top_up")])

        await callback.message.edit_text(
            "Выберите криптовалюту:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        await callback.answer()
        return

    if data.startswith("crypto_"):
        crypto = data.split("_")[1]

        keyboard = [
            [InlineKeyboardButton(text=f"{amount} {crypto}",
                                  callback_data=f"buy_crypto:{crypto}:{amount}")]
            for amount in CRYPTO_PACKAGES[crypto]
        ]
        keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="pay_crypto")])

        await callback.message.edit_text(
            "Выберите сумму:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        await callback.answer()
        return

    if data.startswith("buy_crypto:"):
        _, crypto, amount = data.split(":")
        wallet = CRYPTO_WALLETS[crypto]

        await callback.message.answer(
            f"💰 Оплата {amount} {crypto}\n\n"
            f"Отправьте сумму на кошелек:\n{wallet}\n\n"
            f"После оплаты поиски начисляются вручную."
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
