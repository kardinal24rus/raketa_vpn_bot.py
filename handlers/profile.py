from aiogram import Router
from aiogram.types import CallbackQuery
from keyboards import bottom_keyboard

router = Router()

@router.callback_query(lambda c: c.data == "profile")
async def profile(callback: CallbackQuery):
    profile_text = (
        f"Ваш ID: {callback.from_user.id}\n"
        "Доступно поисков: 0\n"
        "Баланс: $0.00\n"
        "Реферальный баланс: $0.00\n"
        "Дата регистрации: —\n"
        "Вы агент уже: —"
    )
    await callback.message.delete()
    await callback.message.answer(profile_text, reply_markup=bottom_keyboard())
    await callback.answer()