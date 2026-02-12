import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database import init_db

from handlers.start import router as start_router
from handlers.profile import router as profile_router
from handlers.payments import router as payments_router

async def main():
    init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(start_router)
    dp.include_router(profile_router)
    dp.include_router(payments_router)

    print("Бот запущен...")
await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
