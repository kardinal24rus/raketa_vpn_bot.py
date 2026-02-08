import asyncio
from datetime import datetime, timedelta
import aiohttp
import aiosqlite

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ---------------- CONFIG ----------------
BOT_TOKEN = "8523627080:AAEm1A5LGI_W8AGeDOzdZZCd7Qb3xjKuAgM"
CRYPTO_TOKEN = "528577:AA0kJIWTTTkqvjcx5NCij43T7dPFxvBm70b"
CRYPTO_API = "https://pay.crypt.bot/api"

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

# ---------------- DATABASE ----------------
async def init_db():
    async with aiosqlite.connect("db.sqlite3") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            referrer INTEGER,
            sub_until TEXT,
            vpn_key TEXT,
            key_location TEXT,
            key_status TEXT,
            notified_3_days INTEGER DEFAULT 0,
            notified_1_day INTEGER DEFAULT 0,
            notified_today INTEGER DEFAULT 0,
            referral_count INTEGER DEFAULT 0
        )
        """)
        await db.commit()

# ---------------- KEYBOARDS ----------------
def main_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="🚀 Купить", callback_data="buy")
    kb.button(text="🔑 Мой ключ", callback_data="my_key")
    kb.button(text="❓ Помощь", callback_data="help")
    kb.adjust(2, 1)
    return kb.as_markup()

def buy_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="1 месяц – 299₽", callback_data="tariff_1")
    kb.button(text="3 месяца – 799₽", callback_data="tariff_3")
    kb.button(text="12 месяцев – 2499₽", callback_data="tariff_12")
    kb.button(text="⬅ Назад", callback_data="back_main")
    kb.adjust(1)
    return kb.as_markup()

def pay_menu(tariff):
    kb = InlineKeyboardBuilder()
    kb.button(text="💳 Оплатить", callback_data=f"pay_{tariff}")
    kb.button(text="❌ Отменить", callback_data="back_main")
    kb.adjust(1)
    return kb.as_markup()

def my_key_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="Активный ключ", callback_data="key_active")
    kb.button(text="Заменить ключ", callback_data="key_replace")
    kb.button(text="Сменить локацию", callback_data="key_location")
    kb.button(text="Связаться с поддержкой", callback_data="support")
    kb.button(text="⬅ Назад", callback_data="back_main")
    kb.adjust(1)
    return kb.as_markup()

def help_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="Как подключиться", callback_data="how_connect")
    kb.button(text="Связаться с поддержкой", callback_data="support")
    kb.button(text="Оферы и правила", callback_data="rules")
    kb.button(text="Главное меню", callback_data="back_main")
    kb.button(text="🤝 Пригласить друга", callback_data="referral")
    kb.adjust(1)
    return kb.as_markup()

def location_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="🇳🇱 Нидерланды", callback_data="loc_🇳🇱")
    kb.button(text="🇩🇪 Германия", callback_data="loc_🇩🇪")
    kb.button(text="🇫🇮 Финляндия", callback_data="loc_🇫🇮")
    kb.button(text="⬅ Назад", callback_data="my_key")
    kb.adjust(1)
    return kb.as_markup()

# ---------------- CRYPTOBOT ----------------
async def create_invoice(amount: float, description: str):
    headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}
    payload = {"asset": "USDT", "amount": amount, "description": description}
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{CRYPTO_API}/createInvoice", json=payload, headers=headers) as resp:
            data = await resp.json()
            return data["result"]

async def check_invoice(invoice_id: int):
    headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}
    params = {"invoice_ids": invoice_id}
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{CRYPTO_API}/getInvoices", params=params, headers=headers) as resp:
            data = await resp.json()
            return data["result"]["items"][0]

# ---------------- HANDLERS ----------------
@dp.message(CommandStart())
async def start(message: Message):
    ref = None
    if message.text and len(message.text.split()) > 1:
        ref = message.text.split()[1].replace("ref_", "")

    async with aiosqlite.connect("db.sqlite3") as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, referrer, key_status, key_location) VALUES (?, ?, ?, ?)",
            (message.from_user.id, ref, "expired", "🇳🇱 Нидерланды")
        )
        await db.commit()

    await message.answer(
        "🚀 *Ракета VPN*\nНадёжный и быстрый VPN без лишнего шума.",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "buy")
async def buy(call: CallbackQuery):
    await call.message.edit_text("Выберите тариф:", reply_markup=buy_menu())

@dp.callback_query(F.data.startswith("tariff_"))
async def tariff(call: CallbackQuery):
    tariff = call.data.split("_")[1]
    prices = {"1": 5, "3": 13, "12": 40}
    await call.message.edit_text(f"Тариф: {tariff} месяц(ев)\nСтоимость: {prices[tariff]} USDT",
                                 reply_markup=pay_menu(tariff))

@dp.callback_query(F.data.startswith("pay_"))
async def pay(call: CallbackQuery):
    tariff = call.data.split("_")[1]
    prices = {"1": 5, "3": 13, "12": 40}
    invoice = await create_invoice(amount=prices[tariff], description=f"Ракета VPN — {tariff} мес.")

    kb = InlineKeyboardBuilder()
    kb.button(text="💰 Оплатить", url=invoice["pay_url"])
    kb.button(text="🔄 Проверить оплату", callback_data=f"check_{invoice['invoice_id']}_{tariff}")
    kb.adjust(1)

    await call.message.edit_text("Оплатите счёт и нажмите «Проверить оплату»:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("check_"))
async def check(call: CallbackQuery):
    _, invoice_id, tariff = call.data.split("_")
    invoice = await check_invoice(int(invoice_id))
    if invoice["status"] == "paid":
        days = {"1": 30, "3": 90, "12": 365}[tariff]
        until = (datetime.utcnow() + timedelta(days=days)).isoformat()

        async with aiosqlite.connect("db.sqlite3") as db:
            key = f"VPN-{call.from_user.id}-{int(datetime.utcnow().timestamp())}"
            await db.execute("UPDATE users SET sub_until=?, key_status=?, vpn_key=? WHERE user_id=?",
                             (until, "active", key, call.from_user.id))

            cursor = await db.execute("SELECT referrer FROM users WHERE user_id=?", (call.from_user.id,))
            ref = await cursor.fetchone()
            if ref and ref[0]:
                await db.execute("UPDATE users SET sub_until=datetime(sub_until, '+7 days'), referral_count=referral_count+1 WHERE user_id=?",
                                 (ref[0],))
            await db.commit()

        await call.message.edit_text("✅ Оплата прошла успешно! Подписка активирована 🚀", reply_markup=main_menu())
    else:
        await call.answer("❌ Платёж не найден", show_alert=True)

@dp.callback_query(F.data == "my_key")
async def my_key(call: CallbackQuery):
    await call.message.edit_text("Управление ключом:", reply_markup=my_key_menu())

@dp.callback_query(F.data.startswith("key_"))
async def key_actions(call: CallbackQuery):
    async with aiosqlite.connect("db.sqlite3") as db:
        cursor = await db.execute("SELECT vpn_key, key_status, key_location, sub_until FROM users WHERE user_id=?",
                                  (call.from_user.id,))
        user = await cursor.fetchone()
        key, status, loc, sub_until = user
        if status != "active" or not sub_until or datetime.fromisoformat(sub_until) < datetime.utcnow():
            await call.message.edit_text("❌ У вас нет активной подписки", reply_markup=main_menu())
            return

        if call.data == "key_active":
            await call.message.edit_text(f"🔑 Ваш ключ: {key}\nЛокация: {loc}\nДействует до: {sub_until}", reply_markup=my_key_menu())
        elif call.data == "key_replace":
            new_key = f"VPN-{call.from_user.id}-{int(datetime.utcnow().timestamp())}"
            await db.execute("UPDATE users SET vpn_key=? WHERE user_id=?", (new_key, call.from_user.id))
            await db.commit()
            await call.message.edit_text(f"🔑 Ключ заменён: {new_key}", reply_markup=my_key_menu())
        elif call.data == "key_location":
            await call.message.edit_text("Выберите новую локацию:", reply_markup=location_menu())
        elif call.data == "support":
            await call.message.edit_text("📞 Поддержка: @YourSupport", reply_markup=my_key_menu())

@dp.callback_query(F.data.startswith("loc_"))
async def change_location(call: CallbackQuery):
    loc = call.data.split("_")[1]
    async with aiosqlite.connect("db.sqlite3") as db:
        await db.execute("UPDATE users SET key_location=? WHERE user_id=?", (loc, call.from_user.id))
        await db.commit()
    await call.message.edit_text(f"🌍 Локация изменена на {loc}", reply_markup=my_key_menu())

@dp.callback_query(F.data == "help")
async def help_(call: CallbackQuery):
    await call.message.edit_text("Помощь:", reply_markup=help_menu())

@dp.callback_query(F.data == "back_main")
async def back(call: CallbackQuery):
    await call.message.edit_text("Главное меню:", reply_markup=main_menu())

@dp.callback_query(F.data == "referral")
async def referral(call: CallbackQuery):
    ref_link = f"https://t.me/RaketaVPN_bot?start=ref_{call.from_user.id}"
    await call.message.edit_text(f"🤝 Приглашайте друзей и получайте +7 дней VPN\nВаша ссылка:\n{ref_link}",
                                 reply_markup=help_menu())

# ---------------- RUN ----------------
async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
