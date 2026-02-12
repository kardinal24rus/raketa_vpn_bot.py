from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


# --- Стартовая клавиатура ---
def start_inline_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Поиск по неполным данным", callback_data="partial_search")],
            [
                InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile"),
                InlineKeyboardButton(text="🤖 Мои боты", callback_data="my_bots"),
            ],
            [InlineKeyboardButton(text="🤝 Партнёрская программа", callback_data="partner_program")],
        ]
    )


# --- Нижняя клавиатура ---
def bottom_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📂 Показать меню"),
                KeyboardButton(text="👤 Выбрать пользователя"),
            ]
        ],
        resize_keyboard=True,
    )


# --- Клавиатура формы ---
def get_partial_search_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Фамилия", callback_data="input_surname"),
                InlineKeyboardButton(text="Имя", callback_data="input_name"),
                InlineKeyboardButton(text="Отчество", callback_data="input_patronymic"),
            ],
            [
                InlineKeyboardButton(text="День", callback_data="input_day"),
                InlineKeyboardButton(text="Месяц", callback_data="input_month"),
                InlineKeyboardButton(text="Год", callback_data="input_year"),
            ],
            [
                InlineKeyboardButton(text="Возраст от", callback_data="input_age_from"),
                InlineKeyboardButton(text="Возраст", callback_data="input_age"),
                InlineKeyboardButton(text="Возраст до", callback_data="input_age_to"),
            ],
            [
                InlineKeyboardButton(text="Место рождения", callback_data="input_birthplace"),
            ],
            [
                InlineKeyboardButton(text="🗑 Сбросить", callback_data="reset_form"),
                InlineKeyboardButton(text="🔍 Искать", callback_data="search_data"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start"),
            ],
        ]
    )