import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import os
from dotenv import load_dotenv

# ------------------ CONFIG ------------------

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

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
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 Пополнить баланс")],
            [KeyboardButton(text="🔍 Купить запросы")],
            [KeyboardButton(text="👁 Отслеживание")],
            [KeyboardButton(text="🚫 Скрытие данных")],
            [KeyboardButton(text="🎩 Связаться с нами")],
            [KeyboardButton(text="⬅️ Назад к поиску")],
        ],
        resize_keyboard=True
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
        reply_markup=profile_keyboard()
    )


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
