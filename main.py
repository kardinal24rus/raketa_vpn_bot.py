import asyncio
import os
from aiogram import Bot, Dispatcher, Router
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
        "payment_prompt": "💰 Выберите способ оплаты:",
        "package_prompt": "Выберите пакет поисков:"
    },
    "en": {
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

def profile_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💰 Пополнить", callback_data="top_up"),
                InlineKeyboardButton(text="🔍 Купить запросы", callback_data="buy_requests")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back")
            ]
        ]
    )

# ---------------- ROUTER ----------------
router = Router()

# ---------------- START ----------------
@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.set_state(SearchState.form)
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    await state.update_data(balance=0, search_count=0, registration_date=now)

    await message.answer(
        "Добро пожаловать!\n\n"
        "Используйте кнопки ниже 👇",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")]
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

    # --- Профиль ---
    if data == "profile":
        profile_text = (
            f"Ваш ID: {callback.from_user.id}\n"
            f"Доступно поисков: {fsm_data.get('search_count',0)}\n"
            f"Дата регистрации: {fsm_data.get('registration_date','—')}"
        )
        await callback.message.edit_text(profile_text, reply_markup=profile_keyboard())
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
        keyboard = [[InlineKeyboardButton(
            text=f"{p['searches']} поисков — {p['stars']} ⭐",
            callback_data=f"buy_stars:{i}")]
            for i,p in enumerate(STARS_PACKAGES)
        ]
        keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="top_up")])

        await callback.message.edit_text(
            t["package_prompt"],
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        await callback.answer()
        return

    if data.startswith("buy_stars:"):
        idx = int(data.split(":")[1])
        p = STARS_PACKAGES[idx]

        prices = [LabeledPrice(
            label=f"{p['searches']} поисков",
            amount=p["stars"]
        )]

        await callback.message.answer_invoice(
            title="Пополнение поисков",
            description=f"Начисление {p['searches']} поисков",
            payload=f"stars:{idx}",
            currency="XTR",
            prices=prices
        )

        await callback.answer()
        return

# ---------------- PAYMENT HANDLERS ----------------

@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@router.message(lambda message: message.successful_payment is not None)
async def process_successful_payment(message: Message, state: FSMContext):
    payment = message.successful_payment
    payload = payment.invoice_payload

    if payload.startswith("stars:"):
        idx = int(payload.split(":")[1])
        package = STARS_PACKAGES[idx]

        data = await state.get_data()
        current_searches = data.get("search_count", 0)

        new_search_count = current_searches + package["searches"]
        await state.update_data(search_count=new_search_count)

        await message.answer(
            f"✅ Оплата прошла успешно!\n"
            f"Начислено поисков: {package['searches']}\n"
            f"Теперь у вас доступно: {new_search_count}"
        )

# ---------------- MAIN ----------------
async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
