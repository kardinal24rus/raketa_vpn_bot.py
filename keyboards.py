# --- Клавиатура профиля ---
def profile_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💳 Пополнить", callback_data="top_up"),
                InlineKeyboardButton(text="🛒 Купить запросы", callback_data="buy_requests"),
            ],
            [
                InlineKeyboardButton(
                    text="🕵️ Скрытие данных из поиска",
                    callback_data="hide_data"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Отслеживание поисков",
                    callback_data="tracking"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📩 Связаться с нами",
                    callback_data="contact"
                )
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start"),
                InlineKeyboardButton(text="⚙️", callback_data="settings"),
                InlineKeyboardButton(text="🔄", callback_data="refresh_profile"),
            ],
        ]
    )