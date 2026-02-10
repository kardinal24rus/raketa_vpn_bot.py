import asyncio
import os
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime

# ------------------ CONFIG ------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден в переменных окружения")

# ------------------ FSM ------------------
class SearchState(StatesGroup):
    form = State()
    current_input = State()
    language_selection = State()

# ------------------ TRANSLATIONS ------------------
translations = {
    "ru": {
        "surname": "Фамилия", "name": "Имя", "patronymic": "Отчество",
        "day": "День", "month": "Месяц", "year": "Год",
        "age_from": "Возраст от", "age": "Возраст", "age_to": "Возраст до",
        "birthplace": "Место рождения", "country": "Страна",
        "back": "⬅️ Назад", "reset": "🗑 Сбросить", "search": "🔍 Искать",
        "cancel": "Отмена",
        "input_prompt": "Введите {field}:",
        "form_cleared": "Форма очищена:",
        "search_preview": "🔍 Предварительный просмотр поиска:",
        "partial_search": "Вы можете указать любое количество данных.\nЧем больше данных — тем точнее результат.\n\nФорма поиска готова 👇",
        "profile_text": "Ваш ID: {id}\n\nДоступно поисков: {search_count}\nВаш баланс: ${balance:.2f}\nРеферальный баланс: ${referral_balance:.2f}\nДата регистрации: {registration_date}\n(Вы агент уже: {agent_duration})",
        "my_bots": "🤖 Мои боты\n\nУ вас пока нет подключённых ботов.\nЭтот раздел скоро появится 👀",
        "partner_program": "🤝 Партнёрская программа\n\nПриглашайте друзей и получайте бонусы 💰\nРаздел находится в разработке.",
        "top_up": "Баланс пополнен на 100 $ ✅",
        "buy_requests": "Вы купили 1 запрос ✅",
        "cancelled": "Ввод отменён ✅",
        "language_prompt": "Выберите язык / Choose language:",
        "notifications": "Уведомления",
    },
    "en": {
        "surname": "Surname", "name": "Name", "patronymic": "Patronymic",
        "day": "Day", "month": "Month", "year": "Year",
        "age_from": "Age from", "age": "Age", "age_to": "Age to",
        "birthplace": "Birthplace", "country": "Country",
        "back": "⬅️ Back", "reset": "🗑 Reset", "search": "🔍 Search",
        "cancel": "Cancel",
        "input_prompt": "Enter {field}:",
        "form_cleared": "Form cleared:",
        "search_preview": "🔍 Search preview:",
        "partial_search": "You can fill any number of fields.\nThe more data — the more accurate the results.\n\nSearch form ready 👇",
        "profile_text": "Your ID: {id}\n\nSearches available: {search_count}\nYour balance: ${balance:.2f}\nReferral balance: ${referral_balance:.2f}\nRegistration date: {registration_date}\n(Agent for: {agent_duration})",
        "my_bots": "🤖 My bots\n\nYou have no connected bots yet.\nThis section coming soon 👀",
        "partner_program": "🤝 Affiliate program\n\nInvite friends and earn bonuses 💰\nSection in development.",
        "top_up": "Balance topped up by $100 ✅",
        "buy_requests": "You bought 1 request ✅",
        "cancelled": "Input cancelled ✅",
        "language_prompt": "Выберите язык / Choose language:",
        "notifications": "Notifications",
    }
    # Можно добавить другие языки: de, fr, es, cn
}

languages_flags = [
    ("🇷🇺 Русский", "ru"),
    ("🇺🇸 English", "en"),
    ("🇩🇪 Deutsch", "de"),
    ("🇫🇷 Français", "fr"),
    ("🇪🇸 Español", "es"),
    ("🇨🇳 中文", "cn")
]

# ------------------ KEYBOARDS ------------------
def bottom_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📂 Показать меню"), KeyboardButton(text="👤 Выбрать пользователя")]],
        resize_keyboard=True
    )

def get_search_form_keyboard(data: dict, lang="ru"):
    tr = translations[lang]
    def val_or_default(key, default_name):
        return f"{data[key]} ✅" if key in data and data[key] else default_name
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=val_or_default("surname",tr["surname"]), callback_data="input_surname"),
                InlineKeyboardButton(text=val_or_default("name",tr["name"]), callback_data="input_name"),
                InlineKeyboardButton(text=val_or_default("patronymic",tr["patronymic"]), callback_data="input_patronymic"),
            ],
            [
                InlineKeyboardButton(text=val_or_default("day",tr["day"]), callback_data="input_day"),
                InlineKeyboardButton(text=val_or_default("month",tr["month"]), callback_data="input_month"),
                InlineKeyboardButton(text=val_or_default("year",tr["year"]), callback_data="input_year"),
            ],
            [
                InlineKeyboardButton(text=val_or_default("age_from",tr["age_from"]), callback_data="input_age_from"),
                InlineKeyboardButton(text=val_or_default("age",tr["age"]), callback_data="input_age"),
                InlineKeyboardButton(text=val_or_default("age_to",tr["age_to"]), callback_data="input_age_to"),
            ],
            [
                InlineKeyboardButton(text=val_or_default("birthplace",tr["birthplace"]), callback_data="input_birthplace")
            ],
            [
                InlineKeyboardButton(text=val_or_default("country",tr["country"]), callback_data="input_country")
            ],
            [
                InlineKeyboardButton(text=tr["back"], callback_data="back_to_start"),
                InlineKeyboardButton(text=tr["reset"], callback_data="reset_form"),
                InlineKeyboardButton(text=tr["search"], callback_data="search_data")
            ]
        ]
    )

def profile_keyboard(lang="ru"):
    tr = translations[lang]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💰 Пополнить", callback_data="top_up"),
                InlineKeyboardButton(text="🔍 Купить запросы", callback_data="buy_requests")
            ],
            [
                InlineKeyboardButton(text="🚫 Скрытие данных из поиска", callback_data="hide_data")
            ],
            [
                InlineKeyboardButton(text="👁 Отслеживание поисков", callback_data="tracking")
            ],
            [
                InlineKeyboardButton(text="🎩 Связаться с нами", callback_data="contact")
            ],
            [
                InlineKeyboardButton(text=tr["back"], callback_data="back"),
                InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
                InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh")
            ]
        ]
    )

def language_keyboard():
    buttons = []
    for i in range(0, len(languages_flags), 2):
        row = [InlineKeyboardButton(text=languages_flags[i][0], callback_data=f"lang_{languages_flags[i][1]}")]
        if i+1 < len(languages_flags):
            row.append(InlineKeyboardButton(text=languages_flags[i+1][0], callback_data=f"lang_{languages_flags[i+1][1]}"))
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ------------------ ROUTER ------------------
router = Router()

# ------------------ HANDLERS ------------------
@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    data = await state.get_data()
    if "language" not in data:
        await state.set_state(SearchState.language_selection)
        await message.answer(translations["ru"]["language_prompt"], reply_markup=language_keyboard())
    else:
        await show_start_content(message, state, data["language"])

async def show_start_content(message: Message, state: FSMContext, lang="ru"):
    tr = translations.get(lang, translations["ru"])
    await state.set_state(SearchState.form)
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    await state.update_data(balance=0, search_count=0, referral_balance=0,
                            registration_date=now, agent_duration="6 мес., 16 дн.")
    await message.answer(
        "🕵️ Личность:\nИванов Иван Иванович 04.06.1976 - ФИО\n\n"
        "📲 Контакты:\n79999688666 – номер телефона\n79999688666@mail.ru – email\n\n"
        "🚘 Транспорт:\nВ777ОК199 – номер автомобиля\nXTA211550C5106724 – VIN автомобиля\n\n"
        "💬 Социальные сети:\nvk.com/Blindaglaz – Вконтакте\ninstagram.com/Blindaglazk – Instagram\nok.ru/profile/69460 – Одноклассники\n\n"
        "📟 Telegram:\n@@blindaglaz_bot , tg123456 – логин или ID\n\n"
        "📄 Документы:\n/vu 1234567890 – водительские права\n/passport 1234567890 – паспорт\n/snils 12345678901 – СНИЛС\n/inn 123456789012 – ИНН\n\n"
        "🌐 Онлайн-следы:\n/tag хирург москва – поиск по телефонным книгам\nblindaglaz.com или 1.1.1.1 – домен или IP\n\n"
        "🏚 Недвижимость:\n/adr Владивосток, Островская, 9, 94\n77:01:0004042:2387 - кадастровый номер\n\n"
        "🏢 Юридическое лицо:\n/inn 3640214547 – ИНН\n1107462004464 – ОГРН или ОГРНИП\n\n"
        "📸 Отправьте лицо человека, чтобы попробовать найти его.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=tr["search"], callback_data="partial_search")],
                [
                    InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile"),
                    InlineKeyboardButton(text="🤖 Мои боты", callback_data="my_bots")
                ],
                [InlineKeyboardButton(text="🤝 Партнёрская программа", callback_data="partner_program")]
            ]
        )
    )
    await message.answer(reply_markup=bottom_keyboard())

# ------------------ CALLBACK HANDLER ------------------
@router.callback_query(lambda c: True)
async def callback_handler(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    fsm_data = await state.get_data()
    lang = fsm_data.get("language","ru")
    tr = translations.get(lang, translations["ru"])

    # ---------- Выбор языка ----------
    if data.startswith("lang_"):
        selected_lang = data.replace("lang_","")
        await state.update_data(language=selected_lang)
        await callback.message.delete()
        await show_start_content(callback.message, state, selected_lang)
        await callback.answer()
        return

# ------------------ MAIN ------------------
async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
