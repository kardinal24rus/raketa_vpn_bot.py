import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Вставь сюда токен своего бота
TOKEN = "ВАШ_ТОКЕН_БОТА"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Главное меню
main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add(
    KeyboardButton("Поиск по неполным данным"),
    KeyboardButton("Мой профиль")
)
main_menu.add(
    KeyboardButton("Мои боты"),
    KeyboardButton("Партнерская программа")
)

# Кнопки для поиска по неполным данным
search_buttons = ReplyKeyboardMarkup(resize_keyboard=True)
for name in ["Фамилия","Имя","Отчество","День","Месяц","Год","Возраст от","Возраст","Возраст до","Место рождения","Сбросить","Страна","Искать"]:
    search_buttons.add(KeyboardButton(name))
search_buttons.add(KeyboardButton("Отмена"))

# Обработчик команды /start
@dp.message()
async def start(message: types.Message):
    await message.answer(
        "🕵️ «Шерлок». Если информация существует — я её найду.",
        reply_markup=main_menu
    )

# Обработчик кнопок главного меню
@dp.message()
async def menu_handler(message: types.Message):
    text = message.text

    if text == "Поиск по неполным данным":
        await message.answer("Вы можете указать любое количество данных:", reply_markup=search_buttons)

    elif text == "Мой профиль":
        await message.answer(
            "Ваш ID: 123456\nДоступно поисков: 0\nБаланс: $0.00\nДата регистрации: 01.01.2026",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton("Пополнить"), KeyboardButton("Купить запросы")],
                    [KeyboardButton("Скрытие данных из поиска"), KeyboardButton("Отслеживание поисков")],
                    [KeyboardButton("Связаться с нами"), KeyboardButton("Назад")],
                    [KeyboardButton("⚙️"), KeyboardButton("🔄")]
                ],
                resize_keyboard=True
            )
        )

    elif text == "Мои боты":
        await message.answer("Данный раздел на завершающей стадии разработки.", reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton("Назад")]],
            resize_keyboard=True
        ))

    elif text == "Партнерская программа":
        await message.answer(
            "🤝 Партнёрская программа\nВаша реферальная ссылка: https://t.me/ВАШ_БОТ?start=ref",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton("Вывод средств"), KeyboardButton("Назад")]],
                resize_keyboard=True
            )
        )

# Фейковый обработчик для поиска (чтобы бот не падал)
@dp.message()
async def search_handler(message: types.Message):
    if message.text not in ["Поиск по неполным данным","Мой профиль","Мои боты","Партнерская программа"]:
        await message.answer("🔍 Результаты поиска будут здесь (заглушка).")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
