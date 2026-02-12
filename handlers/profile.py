from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards import profile_keyboard
from datetime import datetime

router = Router()


@router.callback_query(F.data == "profile")
async def open_profile(callback: CallbackQuery):

    user_id = callback.from_user.id

    # ---- ВРЕМЕННО (пока без БД) ----
    real_id = user_id
    available_searches = 0
    balance = 0.0
    referral_balance = 0.0
    registration_date = datetime.now()  # позже будет из БД
    # --------------------------------

    now = datetime.now()
    delta = now - registration_date

    months = delta.days // 30
    days = delta.days % 30

    profile_text = (
        f"🆔 Ваш ID: {user_id}\n"
        f"👤 Реальный ID: {real_id}\n\n"
        f"🔎 Доступно поисков: {available_searches}\n"
        f"💰 Баланс: {balance:.2f} ₽\n"
        f"🤝 Реферальный баланс: {referral_balance:.2f} ₽\n"
        f"📅 Дата регистрации: {registration_date.strftime('%d.%m.%Y')}\n\n"
        f"(Вы агент уже {months} мес. {days} дней)"
    )

    await callback.message.answer(
        profile_text,
        reply_markup=profile_keyboard(),
    )

    await callback.answer()