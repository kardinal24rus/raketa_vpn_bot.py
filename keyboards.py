from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ---------------- START INLINE KEYBOARD ----------------
def start_inline_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Поиск по неполным данным", callback_data="partial_search")],
            [
                InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile"),
                InlineKeyboardButton(text="🤖 Мои боты", callback_data="my_bots")
            ],
            [InlineKeyboardButton(text="🤝 Партнёрская программа", callback_data="partner_program")]
        ]
    )

# ---------------- PARTIAL SEARCH KEYBOARD ----------------
def get_partial_search_keyboard(data: dict):
    # data – словарь с текущими значениями формы (можно оставить пустым для начала)
    def val(key, default):
        return f"{data.get(key, '')} ✅" if data.get(key) else default

    return InlineKeyboardMarkup(
        inline_keyboard=[
            # Фамилия, Имя, Отчество
            [
                InlineKeyboardButton(text=val("surname", "Фамилия"), callback_data="input_surname"),
                InlineKeyboardButton(text=val("name", "Имя"), callback_data="input_name"),
                InlineKeyboardButton(text=val("patronymic", "Отчество"), callback_data="input_patronymic")
            ],
            # День, Месяц, Год
            [
                InlineKeyboardButton(text=val("day", "День"), callback_data="input_day"),
                InlineKeyboardButton(text=val("month", "Месяц"), callback_data="input_month"),
                InlineKeyboardButton(text=val("year", "Год"), callback_data="input_year")
            ],
            # Возраст от, Возраст, Возраст до
            [
                InlineKeyboardButton(text=val("age_from", "Возраст от"), callback_data="input_age_from"),
                InlineKeyboardButton(text=val("age", "Возраст"), callback_data="input_age"),
                InlineKeyboardButton(text=val("age_to", "Возраст до"), callback_data="input_age_to")
            ],
            # Место рождения (одна кнопка)
            [
                InlineKeyboardButton(text=val("birthplace", "Место рождения"), callback_data="input_birthplace")
            ],
            # Кнопки назад / сброс / искать
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start"),
                InlineKeyboardButton(text="🗑 Сбросить", callback_data="reset_form"),
                InlineKeyboardButton(text="🔍 Искать", callback_data="search_data")
            ]
        ]
    )