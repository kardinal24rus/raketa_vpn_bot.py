from aiogram import Router
from aiogram.types import CallbackQuery
from keyboards import bottom_keyboard

router = Router()


@router.callback_query(lambda c: c.data == "profile")
async def profile_handler(callback: CallbackQuery):
    await callback.message.delete()

    await callback.message.answer(
        f"Ваш ID: {callback.from_user.id}\nБаланс: 0\nЗапросов: 0",
        reply_markup=bottom_keyboard(),
    )

    await callback.answer()