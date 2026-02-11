from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

router = Router()

@router.callback_query(lambda c: c.data == "profile")
async def profile(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    text = (
        f"Ваш ID: {callback.from_user.id}\n"
        f"Баланс: {data.get('balance', 0)}\n"
        f"Поисков доступно: {data.get('search_count', 0)}"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💰 Пополнить", callback_data="top_up")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start")]
        ]
    )
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()