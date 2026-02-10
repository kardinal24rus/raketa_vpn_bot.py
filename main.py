import asyncio
import os

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# ------------------ CONFIG ------------------

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден в переменных окружения")

# ------------------ FSM ------------------

class SearchState(StatesGroup):
    form = State()

# ------------------ KEYBOARDS ------------------

def bottom_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📂 Показать меню"),
                KeyboardButton(text="👤 Выбрать пользователя"),
            ]
        ],
        resize_keyboard=True
    )


def search_form_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Фамилия"),
                KeyboardButton(text="Имя"),
                KeyboardButton(text="Отчество"),
            ],
            [
                KeyboardButton(text="День"),
                KeyboardButton(text="Месяц"),
                KeyboardButton(text="Год"),
            ],
            [
                KeyboardButton(text="Возраст от"),
                KeyboardButton(text="Возраст"),
                KeyboardButton(text="Возраст до"),
            ],
            [
                KeyboardButton(text="Место рождения"),
            ],
            [
                KeyboardButton(text="🗑 Сбросить"),
                KeyboardButton(text="🇷🇺"),
                KeyboardButton(text="🔍 Искать"),
            ]
        ],
        resize_keyboard=True
    )


def profile_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            # Первая строка: Пополнить / Купить запросы
            [
                InlineKeyboardButton(text="💰 Пополнить", callback_data="top_up"),
                InlineKeyboardButton(text="🔍 Купить запросы", callback_data="buy_requests")
            ],
            # Вторая строка: Скрытие данных
            [
                InlineKeyboardButton(text="🚫 Скрытие данных", callback_data="hide_data")
            ],
            # Третья строка: Отслеживание
            [
                InlineKeyboardButton(text="👁 Отслеживание", callback_data="tracking")
            ],
            # Четвертая строка: Связаться с нами
            [
                InlineKeyboardButton(text="🎩 Связаться с нами", callback_data="contact")
            ],
            # Пятая строка: Назад / Настройки / Обновить
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back"),
                InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
                InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh")
            ]
        ]
    )

# ------------------ ROUTER ------------------

router = Router()

# ------------------ HANDLERS ------------------

@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.set_state(SearchState.form)
    await message.answer(
        "Вы можете указать любое количество данных.\n"
        "Чем больше данных — тем точнее результат.",
        reply_markup=search_form_keyboard()
    )
    await message.answer(
        "Форма поиска готова 👇",
        reply_markup=bottom_keyboard()
    )


@router.message(lambda m: m.text == "📂 Показать меню")
async def show_profile(message: Message):
    await message.answer(
        "👤 *Ваш профиль*\n\n"
        f"ID: `{message.from_user.id}`\n"
        "Доступно поисков: 0\n"
        "Баланс: 0 ₽\n"
        "Реферальный баланс: 0 ₽\n"
        "Дата регистрации: —",
        parse_mode="Markdown",
        reply_markup=profile_keyboard()  # <- теперь inline
    )


@router.callback_query(lambda c: True)  # обработка всех inline кнопок
async def callback_handler(callback: CallbackQuery):
    data = callback.data
    if data == "back":
        # возвращаемся к форме поиска
        await callback.message.edit_reply_markup(None)  # убираем inline клавиатуру
        await callback.message.answer(
            "Возвращаемся к форме поиска 👇",
            reply_markup=search_form_keyboard()
        )
    else:
        # временная заглушка для остальных кнопок
        await callback.answer(f"Вы нажали: {data}", show_alert=True)


@router.message(lambda m: m.text == "⬅️ Назад к поиску")
async def back_to_search(message: Message, state: FSMContext):
    await state.set_state(SearchState.form)
    await message.answer(
        "Возвращаемся к форме поиска 👇",
        reply_markup=search_form_keyboard()
    )


@router.message(lambda m: m.text == "🗑 Сбросить")
async def reset_form(message: Message):
    await message.answer(
        "Форма очищена.",
        reply_markup=search_form_keyboard()
    )


@router.message(lambda m: m.text == "🔍 Искать")
async def search_stub(message: Message):
    await message.answer(
        "🔍 Поиск запущен...\n\n"
        "⚠️ Пока это заглушка.\n"
        "Логика поиска будет подключена дальше."
    )


@router.message(SearchState.form)
async def form_input_stub(message: Message):
    await message.answer(
        f"Поле «{message.text}» выбрано.\n"
        "Ввод данных будет реализован позже."
    )

# ------------------ MAIN ------------------

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
