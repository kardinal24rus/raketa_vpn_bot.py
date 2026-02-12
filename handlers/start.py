from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from keyboards import start_inline_keyboard, get_partial_search_keyboard
from states import SearchState

router = Router()

FORM_TEXT = (
    "Заполните известные данные.\n"
    "Все поля необязательны.\n"
)

FIELDS = {
    "input_surname": "surname",
    "input_name": "name",
    "input_patronymic": "patronymic",
    "input_day": "day",
    "input_month": "month",
    "input_year": "year",
    "input_age_from": "age_from",
    "input_age": "age",
    "input_age_to": "age_to",
    "input_birthplace": "birthplace",
}


# --- START ---
@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Добро пожаловать 👋\n\nВыберите действие:",
        reply_markup=start_inline_keyboard(),
    )


# --- Открытие формы ---
@router.callback_query(F.data == "partial_search")
async def open_form(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SearchState.form)
    await state.update_data({})

    await callback.message.answer(
        FORM_TEXT,
        reply_markup=get_partial_search_keyboard(),
    )

    await callback.answer()


# --- Возврат назад ---
@router.callback_query(F.data == "back_to_start")
async def back_to_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    await callback.message.answer(
        "Главное меню 👇",
        reply_markup=start_inline_keyboard(),
    )

    await callback.answer()


# --- Выбор поля ---
@router.callback_query(F.data.in_(FIELDS.keys()))
async def choose_field(callback: CallbackQuery, state: FSMContext):
    field_name = FIELDS[callback.data]

    await state.set_state(SearchState.current_input)
    await state.update_data(current_field=field_name)

    await callback.message.answer("Введите значение:")
    await callback.answer()


# --- Ввод значения ---
@router.message(SearchState.current_input)
async def save_value(message: Message, state: FSMContext):
    data = await state.get_data()
    field = data.get("current_field")

    if field:
        await state.update_data({field: message.text})

    await state.set_state(SearchState.form)

    await message.answer(
        "Данные сохранены.\n\n" + FORM_TEXT,
        reply_markup=get_partial_search_keyboard(),
    )


# --- Сброс формы ---
@router.callback_query(F.data == "reset_form")
async def reset_form(callback: CallbackQuery, state: FSMContext):
    await state.update_data({})

    await callback.message.answer(
        "Форма очищена.\n\n" + FORM_TEXT,
        reply_markup=get_partial_search_keyboard(),
    )

    await callback.answer()


# --- Предпросмотр ---
@router.callback_query(F.data == "search_data")
async def preview_search(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    text = "Предпросмотр запроса:\n\n"

    has_data = False
    for key, value in data.items():
        if key != "current_field" and value:
            text += f"{key}: {value}\n"
            has_data = True

    if not has_data:
        text += "Вы ничего не заполнили."

    await callback.message.answer(text)
    await callback.answer()