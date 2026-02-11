from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from states import SearchState

router = Router()

@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    # Сохраняем язык по умолчанию
    await state.set_state(SearchState.language_selection)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
             InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
        ]
    )
    await message.answer("Выберите язык / Choose language:", reply_markup=from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

router = Router()

# ------------------ Кнопки под сообщением ------------------
def start_inline_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Поиск по неполным данным", callback_data="partial_search")],
            [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")],
            [InlineKeyboardButton(text="🤖 Мои боты", callback_data="my_bots")],
            [InlineKeyboardButton(text="🤝 Партнёрская программа", callback_data="partner_program")],
        ]
    )

# ------------------ Сообщение старта ------------------
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
    "tiktok.com/@shellack – Tiktok\n"
    "instagram.com/mizim – Instagram\n"
    "ok.ru/profile/58460 – Одноклассники\n\n"
    "📟 Telegram:\n"
    "@glazik, tg123456 – логин или ID\n\n"
    "📄 Документы:\n"
    "/vu 1234567890 – водительские права\n"
    "/passport 1234567890 – паспорт\n"
    "/snils 12345678901 – СНИЛС\n"
    "/inn 123456789012 – ИНН\n\n"
    "🌐 Онлайн-следы:\n"
    "/tag хирург москва – поиск по телефонным книгам\n"
    "sherlock.com или 1.1.1.1 – домен или IP\n\n"
    "🏚 Недвижимость:\n"
    "/adr Москва, Островитянова, 9к4, 94\n"
    "77:01:0004042:6987 – кадастровый номер\n\n"
    "🏢 Юридическое лицо:\n"
    "/inn 2540214547 – ИНН\n"
    "1107449004464 – ОГРН или ОГРНИП\n\n"
    "📸 Отправьте лицо человека, чтобы попробовать найти его."
)

# ------------------ Хэндлер /start ------------------
@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await message.answer(
        START_TEXT,
        reply_markup=start_inline_keyboard()
    from handlers.start import router as start_router