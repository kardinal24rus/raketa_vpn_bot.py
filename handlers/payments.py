from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

@router.callback_query(lambda c: c.data == "buy_requests")
async def buy_requests(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⭐ Telegram Stars", callback_data="pay_stars")],
            [InlineKeyboardButton(text="💰 Криптовалюта", callback_data="pay_crypto")],
        ]
    )
    await callback.message.answer("💰 Выберите способ оплаты:", reply_markup=kb)
    await callback.answer()
