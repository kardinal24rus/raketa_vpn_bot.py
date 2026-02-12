from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from keyboards import bottom_keyboard

router = Router()

# Простейший каркас кнопки «Пополнить»
@router.callback_query(lambda c: c.data == "top_up")
async def top_up_callback(callback: CallbackQuery, state: FSMContext):
    # Текст для примера
    text = (
        "💰 Выберите способ оплаты:\n"
        "Пока это пример, позже добавим интеграцию с платежной системой.\n\n"
        "Выберите пакет поисков:"
    )

    # Кнопки выбора пакета (пример)
    package_buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="10 поисков – $5", callback_data="package_10")],
        [InlineKeyboardButton(text="50 поисков – $20", callback_data="package_50")],
        [InlineKeyboardButton(text="100 поисков – $35", callback_data="package_100")],
    ])

    await callback.message.delete()
    await callback.message.answer(text, reply_markup=package_buttons)
    await callback.answer()

# Обработка выбора пакета (пока просто подтверждение)
@router.callback_query(lambda c: c.data.startswith("package_"))
async def package_selected(callback: CallbackQuery, state: FSMContext):
    package = callback.data.replace("package_", "")
    await callback.message.answer(f"Вы выбрали пакет: {package} (это пока тест)")
    await callback.answer()