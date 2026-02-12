from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from keyboards import start_inline_keyboard, get_partial_search_keyboard
from states import SearchState

router = Router()

# 🔹 БОЛЬШОЙ СТАРТОВЫЙ ТЕКСТ
START_TEXT = (
    "🕵️ Личность:\n"
    "Петросян Евгений Анатольевич 04.06.1976 – ФИО\n\n"
    "📲 Контакты:\n"
    "79999688666 – номер телефона\n"
    "79999688666@mail.ru – email\n\n"
    "🚘 Транспорт:\n"
    "В395ОК199 – номер автомобиля\n"
    "XTA211440C5106924 – VIN автомобиля\n\n"
    "💬 Социальные сети:\n"
    "vk.com/sherpik – Вконтакте\n"
    "tiktok.com/@shellack – TikTok\n"
    "instagram.com/mizim – Instagram\n"
    "ok.ru/profile/58460 – Одноклассники\n\n"
    "📟 Telegram:\n"
    "@glazik, tg123456 – логин или ID\n\n"
    "📄 Документы:\n"
    "/vu 1234567890 – водительские права\n"
    "/passport 1234567890 – паспорт\n"
    "/snils 12345678901 – СНИЛС\n"
    "/inn 2540214547 – ИНН\n\n"
    "🌐 Онлайн-следы:\n"
    "/tag хирург москва – поиск\n"
    "sherlock.com или 1.1.1.1 – домен или IP\n\n"
    "🏚 Недвижимость:\n"
    "/adr Москва, Островитянова, 9к4, 94\n"
    "77:01:0004042:6987 – кадастровый номер\n\n"
    "🏢 Юридическое лицо:\n"
    "/inn 2540214547 – ИНН\n"
    "1107449004464 – ОГРН или ОГРНИП\n\n"
    "📸 Отправьте лицо человека, чтобы попробовать найти его."
)

# 🔹 ТЕКСТ ФОРМЫ
FORM_TEXT = (
    "Вы можете узнать любое количество данных — фамилия, имя, отчество,\n"
    "дату или год рождения, возраст, место рождения и так далее.\n"
    "Достаточно заполнить то, что у вас есть.\n\n"
    "Все поля необязательны."
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
        START_TEXT,
        reply_markup=start_inline_keyboard(),
    )


# --- Открыть форму ---
@router.callback_query(F.data == "partial_search")
async def open_form(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SearchState.form)
    await state.update_data({})

    await callback.message.answer(
        FORM_TEXT,
        reply_markup=get_partial_search_keyboard(),
    )

    await callback.answer()


# --- Назад ---
@router.callback_query(F.data == "back_to_start")
async def back_to_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    await callback.message.answer(
        START_TEXT,
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


# --- Сохранение значения ---
@router.message(SearchState.current_input)
async def save_value(message: Message, state: FSMContext):
    data = await state.get_data()
    field = data.get("current_field")

    if field:
        await state.update_data({field: message.text})

    await state.set_state(SearchState.form)

    await message.answer(
        FORM_TEXT,
        reply_markup=get_partial_search_keyboard(),
    )


# --- Сброс ---
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

    text = "🔍 Предпросмотр запроса:\n\n"

    has_data = False
    for key, value in data.items():
        if key != "current_field" and value:
            text += f"{key}: {value}\n"
            has_data = True

    if not has_data:
        text += "Вы ничего не заполнили."

    await callback.message.answer(text)
    await callback.answer()