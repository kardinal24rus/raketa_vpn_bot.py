import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
import asyncio
import os

API_TOKEN = os.getenv("BOT_TOKEN")  # токен бота берём из переменных окружения

if not API_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан в переменных окружения!")

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Создание объектов бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Простейший хендлер команды /start
@dp.message(Command(commands=["start"]))
async def start_command(message: Message):
    await message.answer("Привет! Бот успешно запущен 🚀")

async def main():
    try:
        logging.info("Бот запускается...")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
