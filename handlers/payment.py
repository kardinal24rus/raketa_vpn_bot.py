from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    LabeledPrice,
    PreCheckoutQuery,
)
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

router = Router()

# =========================
# ТАРИФЫ
# =========================

PACKAGES = {
    "p1": {"searches": 1, "stars": 50},
    "p10": {"searches": 10, "stars": 250},
    "p25": {"searches": 25, "stars": 500},
    "p65": {"searches": 65, "stars": 1000},
    "p600": {"searches": 600, "stars": 8000},
    "p1200": {"searches": 1200, "stars": 15000},
    "p10000": {"searches": 10000, "stars": 25000},
}

# =========================
# FSM ОПЛАТЫ
# =========================

class PaymentState(StatesGroup):
    choose_method = State()
    choose_package = State()

# =========================
# КНОПКА «ПОПОЛНИТЬ»
# =========================

@router.callback_query(F.data == "top_up")
async def top_up(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PaymentState.choose_method)

    await callback.message.edit_text(
        "💰 Выберите способ оплаты:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⭐ Оплата звёздами", callback_data="pay_stars")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="profile")],
            ]
        )
    )
    await callback.answer()

# =========================
# ВЫБОР ТАРИФА
# =========================

@router.callback_query(F.data == "pay_stars")
async def choose_stars_package(callback: CallbackQuery):
    keyboard = []

    for key, pack in PACKAGES.items():
        keyboard.append([
            InlineKeyboardButton(
                text=f"🔍 {pack['searches']} поисков — {pack['stars']} ⭐",
                callback_data=f"buy_stars:{key}"
            )
        ])

    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="top_up")])

    await callback.message.edit_text(
        "Выберите пакет:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()

# =========================
# СОЗДАНИЕ INVOICE (STARS)
# =========================

@router.callback_query(F.data.startswith("buy_stars:"))
async def buy_stars(callback: CallbackQuery):
    package_key = callback.data.split(":")[1]
    pack = PACKAGES[package_key]

    prices = [
        LabeledPrice(
            label=f"{pack['searches']} поисков",
            amount=pack["stars"]
        )
    ]

    await callback.message.answer_invoice(
        title="Пополнение поисков",
        description=f"Начисление {pack['searches']} поисков",
        payload=f"stars:{package_key}",
        provider_token="",  # для Stars не нужен
        currency="XTR",
        prices=prices
    )
    await callback.answer()

# =========================
# PRE-CHECKOUT
# =========================

@router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

# =========================
# УСПЕШНАЯ ОПЛАТА
# =========================

@router.message(F.successful_payment)
async def successful_payment(message: Message, state: FSMContext):
    payload = message.successful_payment.invoice_payload

    if payload.startswith("stars:"):
        package_key = payload.split(":")[1]
        searches = PACKAGES[package_key]["searches"]

        data = await state.get_data()
        current_searches = data.get("search_count", 0)

        await state.update_data(search_count=current_searches + searches)

        await message.answer(
            f"✅ Оплата прошла успешно\n"
            f"🔍 Начислено: {searches} поисков\n"
            f"📊 Всего доступно: {current_searches + searches}"
        )
