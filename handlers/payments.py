from aiogram import Router
from aiogram.types import CallbackQuery

router = Router()

@router.callback_query(lambda c: c.data == "buy_requests")
async def buy_requests(callback: CallbackQuery):
    await callback.message.answer("Здесь будет логика покупки запросов.")
    await callback.answer()