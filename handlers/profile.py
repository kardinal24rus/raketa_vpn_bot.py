from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards import bottom_keyboard

router = Router()

@router.callback_query(lambda c: c.data == "profile")
async def profile_callback(callback: CallbackQuery, state: FSMContext):
    fsm_data = await state.get_data()
    profile_text = (
        f"Ваш ID: {callback.from_user.id}\n\n"
        f"Доступно поисков: {fsm_data.get('search_count',0)}\n"
        f"Ваш баланс: ${fsm_data.get('balance',0):.2f}\n"
        f"Реферальный баланс: ${fsm_data.get('referral_balance',0):.2f}\n"
        f"Дата регистрации: {fsm_data.get('registration_date','—')}\n"
        f"(Вы агент уже: {fsm_data.get('agent_duration','—')})"
    )
    await callback.message.delete()
    await callback.message.answer(profile_text, reply_markup=bottom_keyboard())
    await callback.answer()
