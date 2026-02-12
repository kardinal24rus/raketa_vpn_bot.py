from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from keyboards import start_inline_keyboard, get_partial_search_keyboard
from states import SearchState

router = Router()

START_TEXT = "Добро пожаловать 👋"

FORM_TEXT = (
    "Вы можете узнать любое количество данных.\n"
    "Заполните только то, что у вас есть.\n\n"
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


# --- /start ---
@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(START_TEXT, reply_markup=start_inline_keyboard())


# --- Открыть форму ---
@router.callback_query(F.data == "partial_search")
async def open_form(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SearchState.form)
    await state.update_data({})
    await callback.message.delete()

    await callback.message.answer(
        FORM_TEXT,
        reply_markup=get_partial_search_keyboard({})
    )
    await callback.answer()


# --- Нажатие на кнопку поля ---
@router.callback_query(F.data.in_(FIELDS.keys()))
async def select_field(callback: CallbackQuery, state: FSMContext):
    field_key = FIELDS[callback.data]

    await state.set_state(SearchState.current_input)
    await state.update_data(current_field=field_key)

    await callback.message.answer("Введите значение:")
    await callback.answer()


# --- Ввод значения ---
@router.message(SearchState.current_input)
async def save_field_value(message: Message, state: FSMContext):
    data = await state.get_data()
    field = data.get("current_field")

    if field:
        await state.update_data({field: message.text})

    new_data = await state.get_data()

    await state.set_state(SearchState.form)

    await message.answer(
        FORM_TEXT,
        reply_markup=get_partial_search_keyboard(new_data)
    )


# --- Сброс ---
@router.callback_query(F.data == "reset_form")
async def reset_form(callback: CallbackQuery, state: FSMContext):
    await state.update_data({})
    await state.set_state(SearchState.form)

    await callback.message.edit_text(
        FORM_TEXT,
        reply_markup=get_partial_search_keyboard({})
    )
    await callback.answer("Форма очищена")


# --- Искать ---
@router.callback_query(F.data == "search_data")
async def preview_search(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    preview = "🔍 Предпросмотр запроса:\n\n"

    for key, value in data.items():
        if key not in ["current_field"] and value:
            preview += f"{key}: {value}\n"

    if preview.strip() == "🔍 Предпросмотр запроса:":
        preview += "Вы ничего не заполнили."

    await callback.message.answer(preview)
    await callback.answer()