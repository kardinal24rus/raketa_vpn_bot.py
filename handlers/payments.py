from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

@router.callback_query(lambda c: c.data == "top_up")
async def top_up(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⭐ Telegram Stars", callback_data="pay_stars")],
            [InlineKeyboardButton(text="💰 Криптовалюта", callback_data="pay_crypto")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="profile")]
        ]
    )
    await callback.message.edit_text("Выберите способ оплаты:", reply_markup=kb)
    await callback.answer()