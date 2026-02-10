import asyncio
import os

from aiogram import Bot, Dispatcher, Router
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
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
            [
                InlineKeyboardButton(text="💰 Пополнить", callback_data="top_up"),
                InlineKeyboardButton(text="🔍 Купить запросы", callback_data="buy_requests")
            ],
            [
                InlineKeyboardButton(text="🚫 Скрытие данных", callback_data="hide_data")
            ],
            [
                InlineKeyboardButton(text="👁 Отслеживание", callback_data="tracking")
            ],
            [
                InlineKeyboardButton(text="🎩 Связаться с нами", callback_data="contact")
            ],
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
    await state.update_data(balance=0, search_count=0, referral_balance=0)

    await message.answer(
        "🕵️ Личность:\n"
        "Иванов Иван Иванович 04.06.1976 - ФИО\n\n"
        "📲 Контакты:\n"
        "79999688666 – номер телефона\n"
        "79999688666@mail.ru – email\n\n"
        "🚘 Транспорт:\n"
        "В777ОК199 – номер автомобиля\n"
        "XTA211550C5106724 – VIN автомобиля\n\n"
        "💬 Социальные сети:\n"
        "vk.com/Blindaglaz – Вконтакте\n"
        "tiktok.com/@Blindaglaz – Tiktok\n"
        "instagram.com/Blindaglazk – Instagram\n"
        "ok.ru/profile/69460 – Одноклассники\n\n"
        "📟 Telegram:\n"
        "@@blindaglaz_bot , tg123456 – логин или ID\n\n"
        "📄 Документы:\n"
        "/vu 1234567890 – водительские права\n"
        "/passport 1234567890 – паспорт\n"
        "/snils 12345678901 – СНИЛС\n"
        "/inn 123456789012 – ИНН\n\n"
        "🌐 Онлайн-следы:\n"
        "/tag хирург москва – поиск по телефонным книгам\n"
        "blindaglaz.com или 1.1.1.1 – домен или IP\n\n"
        "🏚 Недвижимость:\n"
        "/adr Владивосток, Островская, 9, 94\n"
        "77:01:0004042:2387 - кадастровый номер\n\n"
        "🏢 Юридическое лицо:\n"
        "/inn 3640214547 – ИНН\n"
        "1107462004464 – ОГРН или ОГРНИП\n\n"
        "📸 Отправьте лицо человека, чтобы попробовать найти его.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Поиск по неполным данным", callback_data="partial_search")],
                [
                    InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile"),
                    InlineKeyboardButton(text="🤖 Мои боты", callback_data="my_bots")
                ],
                [InlineKeyboardButton(text="🤝 Партнёрская программа", callback_data="partner_program")]
            ]
        )
    )

    await message.answer(
        "Вы можете указать любое количество данных.\n"
        "Чем больше данных — тем точнее результат.",
        reply_markup=search_form_keyboard()
    )

    await message.answer(
        "Форма поиска готова 👇",
        reply_markup=bottom_keyboard()
    )


@router.callback_query(lambda c: True)
async def callback_handler(callback: CallbackQuery, state: FSMContext):
    data = callback.data

    if data == "back":
        await callback.message.edit_reply_markup(None)
        await callback.message.answer(
            "Возвращаемся к форме поиска 👇",
            reply_markup=search_form_keyboard()
        )

    elif data == "refresh":
        fsm_data = await state.get_data()
        balance = fsm_data.get("balance", 0)
        search_count = fsm_data.get("search_count", 0)
        referral_balance = fsm_data.get("referral_balance", 0)

        profile_text = (
            f"👤 *Ваш профиль*\n\n"
            f"ID: `{callback.from_user.id}`\n"
            f"Доступно поисков: {search_count}\n"
            f"Баланс: {balance} ₽\n"
            f"Реферальный баланс: {referral_balance} ₽\n"
            "Дата регистрации: —"
        )

        await callback.message.edit_text(
            profile_text,
            parse_mode="Markdown",
            reply_markup=profile_keyboard()
        )
        await callback.answer("Профиль обновлён ✅", show_alert=False)

    elif data == "top_up":
        fsm_data = await state.get_data()
        balance = fsm_data.get("balance", 0) + 100
        await state.update_data(balance=balance)
        await callback.answer("Баланс пополнен на 100 ₽ ✅", show_alert=True)

    elif data == "buy_requests":
        fsm_data = await state.get_data()
        search_count = fsm_data.get("search_count", 0) + 1
        await state.update_data(search_count=search_count)
        await callback.answer("Вы купили 1 запрос ✅", show_alert=True)

    else:
        await callback.answer(f"Вы нажали: {data}", show_alert=True)


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
        "⚠️ Пока это заглушка."
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
