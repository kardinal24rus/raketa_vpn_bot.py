from aiogram import Router, F
from aiogram.types import (
    CallbackQuery, Message,
    InlineKeyboardMarkup, InlineKeyboardButton,
    LabeledPrice, PreCheckoutQuery
)

router = Router()

# =========================
# НАСТРОЙКИ
# =========================

TELEGRAM_PROVIDER_TOKEN = "PASTE_YOUR_PROVIDER_TOKEN"
CRYPTO_PAY_LINK = "https://t.me/CryptoBot?start=YOUR_ID"

# searches — сколько поисков
# price — цена в копейках (RUB)
PACKAGES = {
    "p1": {"searches": 1, "price": 100},
    "p10": {"searches": 10, "price": 500},
    "p25": {"searches": 25, "price": 1000},
    "p65": {"searches": 65, "price": 2000},
}

# =========================
# ВЫБОР СПОСОБА ОПЛАТЫ
# =========================
@router.callback_query(F.data == "top_up")
async def top_up(callback: CallbackQuery):
    await callback.message.edit_text(
        "💰 Выберите способ оплаты:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Банковская карта", callback_data="pay_tg")],
            [InlineKeyboardButton(text="🪙 Криптовалюта", callback_data="pay_crypto")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="profile")]
        ])
    )
    await callback.answer()

# =========================
# ВЫБОР ПАКЕТА
# =========================
def packages_keyboard(prefix: str):
    kb = []
    for key, pack in PACKAGES.items():
        kb.append([
            InlineKeyboardButton(
                text=f"{pack['searches']} поисков",
                callback_data=f"{prefix}:{key}"
            )
        ])
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="top_up")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

@router.callback_query(F.data == "pay_tg")
async def pay_tg(callback: CallbackQuery):
    await callback.message.edit_text(
        "💳 Выберите пакет:",
        reply_markup=packages_keyboard("buy_tg")
    )
    await callback.answer()

# =========================
# TELEGRAM PAYMENTS
# =========================
@router.callback_query(F.data.startswith("buy_tg:"))
async def buy_tg(callback: CallbackQuery):
    key = callback.data.split(":")[1]
    pack = PACKAGES[key]

    await callback.message.answer_invoice(
        title="Покупка поисков",
        description=f"{pack['searches']} поисков",
        payload=f"tg:{key}",
        provider_token=TELEGRAM_PROVIDER_TOKEN,
        currency="RUB",
        prices=[
            LabeledPrice(
                label="Поиски",
                amount=pack["price"]
            )
        ],
    )
    await callback.answer()

@router.pre_checkout_query()
async def pre_checkout(pre: PreCheckoutQuery):
    await pre.answer(ok=True)

@router.message(F.successful_payment)
async def successful_payment(message: Message):
    payload = message.successful_payment.invoice_payload
    key = payload.split(":")[1]
    searches = PACKAGES[key]["searches"]

    # TODO: начисление поисков пользователю (БД)
    # add_searches(user_id=message.from_user.id, count=searches)

    await message.answer(
        f"✅ Оплата прошла успешно\n"
        f"🔍 Начислено поисков: {searches}"
    )

# =========================
# CRYPTO
# =========================
@router.callback_query(F.data == "pay_crypto")
async def pay_crypto(callback: CallbackQuery):
    await callback.message.edit_text(
        "🪙 Оплата криптовалютой\n\n"
        "Перейдите по ссылке и оплатите.\n"
        "После оплаты напишите в поддержку.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💎 Оплатить", url=CRYPTO_PAY_LINK)],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="top_up")]
        ])
    )
    await callback.answer()
