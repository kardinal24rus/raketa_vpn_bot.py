import asyncio
import os
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
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
    current_input = State()  # Для ввода конкретного поля

# ------------------ KEYBOARDS ------------------

def bottom_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="?? Показать меню"), KeyboardButton(text="?? Выбрать пользователя")]
        ],
        resize_keyboard=True
    )

def get_search_form_keyboard(data: dict):
    # Формируем кнопки с учётом введённых данных
    def val_or_default(key):
        return f"{data[key]} ?" if key in data and data[key] else key.replace("_", " ").capitalize()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=val_or_default("surname"), callback_data="input_surname"),
                InlineKeyboardButton(text=val_or_default("name"), callback_data="input_name"),
                InlineKeyboardButton(text=val_or_default("patronymic"), callback_data="input_patronymic"),
            ],
            [
                InlineKeyboardButton(text=val_or_default("day"), callback_data="input_day"),
                InlineKeyboardButton(text=val_or_default("month"), callback_data="input_month"),
                InlineKeyboardButton(text=val_or_default("year"), callback_data="input_year"),
            ],
            [
                InlineKeyboardButton(text=val_or_default("age_from"), callback_data="input_age_from"),
                InlineKeyboardButton(text=val_or_default("age"), callback_data="input_age"),
                InlineKeyboardButton(text=val_or_default("age_to"), callback_data="input_age_to"),
            ],
            [
                InlineKeyboardButton(text=val_or_default("birthplace"), callback_data="input_birthplace")
            ],
            [
                InlineKeyboardButton(text=val_or_default("country"), callback_data="input_country")
            ],
            [
                InlineKeyboardButton(text="?? Назад", callback_data="back_to_start"),
                InlineKeyboardButton(text="?? Сбросить", callback_data="reset_form"),
                InlineKeyboardButton(text="?? Искать", callback_data="search_data")
            ]
        ]
    )

def profile_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="?? Пополнить", callback_data="top_up"),
                InlineKeyboardButton(text="?? Купить запросы", callback_data="buy_requests")
            ],
            [
                InlineKeyboardButton(text="?? Скрытие данных из поиска", callback_data="hide_data")
            ],
            [
                InlineKeyboardButton(text="?? Отслеживание поисков", callback_data="tracking")
            ],
            [
                InlineKeyboardButton(text="?? Связаться с нами", callback_data="contact")
            ],
            [
                InlineKeyboardButton(text="?? Назад", callback_data="back"),
                InlineKeyboardButton(text="?? Настройки", callback_data="settings"),
                InlineKeyboardButton(text="?? Обновить", callback_data="refresh")
            ]
        ]
    )

# ------------------ ROUTER ------------------

router = Router()

# ------------------ HANDLERS ------------------

@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.set_state(SearchState.form)
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    await state.update_data(balance=0, search_count=0, referral_balance=0,
                            registration_date=now, agent_duration="6 мес., 16 дн.")
    await message.answer(
        "??? Личность:\n"
        "Иванов Иван Иванович 04.06.1976 - ФИО\n\n"
        "?? Контакты:\n"
        "79999688666 – номер телефона\n"
        "79999688666@mail.ru – email\n\n"
        "?? Транспорт:\n"
        "В777ОК199 – номер автомобиля\n"
        "XTA211550C5106724 – VIN автомобиля\n\n"
        "?? Социальные сети:\n"
        "vk.com/Blindaglaz – Вконтакте\n"
        "instagram.com/Blindaglazk – Instagram\n"
        "ok.ru/profile/69460 – Одноклассники\n\n"
        "?? Telegram:\n"
        "@@blindaglaz_bot , tg123456 – логин или ID\n\n"
        "?? Документы:\n"
        "/vu 1234567890 – водительские права\n"
        "/passport 1234567890 – паспорт\n"
        "/snils 12345678901 – СНИЛС\n"
        "/inn 123456789012 – ИНН\n\n"
        "?? Онлайн-следы:\n"
        "/tag хирург москва – поиск по телефонным книгам\n"
        "blindaglaz.com или 1.1.1.1 – домен или IP\n\n"
        "?? Недвижимость:\n"
        "/adr Владивосток, Островская, 9, 94\n"
        "77:01:0004042:2387 - кадастровый номер\n\n"
        "?? Юридическое лицо:\n"
        "/inn 3640214547 – ИНН\n"
        "1107462004464 – ОГРН или ОГРНИП\n\n"
        "?? Отправьте лицо человека, чтобы попробовать найти его.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="?? Поиск по неполным данным", callback_data="partial_search")],
                [
                    InlineKeyboardButton(text="?? Мой профиль", callback_data="profile"),
                    InlineKeyboardButton(text="?? Мои боты", callback_data="my_bots")
                ],
                [InlineKeyboardButton(text="?? Партнёрская программа", callback_data="partner_program")]
            ]
        )
    )
    await message.answer("Выберите действие ниже:", reply_markup=bottom_keyboard())

# ------------------ CALLBACK HANDLER ------------------

@router.callback_query(lambda c: True)
async def callback_handler(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    fsm_data = await state.get_data()
    balance = fsm_data.get("balance", 0)
    search_count = fsm_data.get("search_count", 0)
    referral_balance = fsm_data.get("referral_balance", 0)
    registration_date = fsm_data.get("registration_date", "—")
    agent_duration = fsm_data.get("agent_duration", "—")

    # ---------- Поиск по неполным данным ----------
    if data == "partial_search":
        await state.set_state(SearchState.form)
        await callback.message.delete()
        await callback.message.answer(
            "Вы можете указать любое количество данных.\n"
            "Чем больше данных — тем точнее результат.\n\n"
            "Форма поиска готова ??",
            reply_markup=get_search_form_keyboard(fsm_data)
        )
        await callback.answer()
    # ---------- Ввод полей ----------
    elif data.startswith("input_"):
        field = data.replace("input_", "")
        await state.set_state(SearchState.current_input)
        await state.update_data(current_field=field)
        await callback.message.answer(f"Введите {field.replace('_', ' ')}:", reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Отмена", callback_data="cancel_input")]]
        ))
        await callback.answer()
    # ---------- Отмена ввода ----------
    elif data == "cancel_input":
        await state.set_state(SearchState.form)
        fsm_data = await state.get_data()
        await callback.message.delete()
        await callback.message.answer(
            "Форма поиска:",
            reply_markup=get_search_form_keyboard(fsm_data)
        )
        await callback.answer("Ввод отменён ?")
    # ---------- Назад ----------
    elif data == "back_to_start" or data == "back":
        await callback.message.delete()
        await start(callback.message, state)
        await callback.answer()
    # ---------- Сбросить форму ----------
    elif data == "reset_form":
        await state.update_data({
            "surname": "", "name": "", "patronymic": "", "day": "", "month": "", "year": "",
            "age_from": "", "age": "", "age_to": "", "birthplace": "", "country": ""
        })
        await state.set_state(SearchState.form)
        await callback.message.delete()
        await callback.message.answer(
            "Форма очищена:",
            reply_markup=get_search_form_keyboard({})
        )
        await callback.answer()
    # ---------- Искать ----------
    elif data == "search_data":
        search_preview = "\n".join([f"{k}: {v}" for k,v in fsm_data.items() if v and k != "current_field"])
        search_preview = search_preview or "?? Пока ничего не введено"
        await callback.message.answer(f"?? Предварительный просмотр поиска:\n{search_preview}")
        await callback.answer()
    # ---------- Профиль ----------
    elif data == "profile":
        profile_text = (
            f"Ваш ID: {callback.from_user.id}\n\n"
            f"Доступно поисков: {search_count}\n"
            f"Ваш баланс: ${balance:.2f}\n"
            f"Реферальный баланс: ${referral_balance:.2f}\n"
            f"Дата регистрации: {registration_date}\n"
            f"(Вы агент уже: {agent_duration})"
        )
        await callback.message.delete()
        await callback.message.answer(profile_text, reply_markup=profile_keyboard())
        await callback.answer()
    # ---------- Мои боты ----------
    elif data == "my_bots":
        await callback.message.delete()
        await callback.message.answer(
            "?? Мои боты\n\nУ вас пока нет подключённых ботов.\nЭтот раздел скоро появится ??"
        )
        await callback.answer()
    # ---------- Партнёрская программа ----------
    elif data == "partner_program":
        await callback.message.delete()
        await callback.message.answer(
            "?? Партнёрская программа\n\nПриглашайте друзей и получайте бонусы ??\nРаздел находится в разработке."
        )
        await callback.answer()
    # ---------- Обновление профиля ----------
    elif data == "refresh":
        profile_text = (
            f"Ваш ID: {callback.from_user.id}\n\n"
            f"Доступно поисков: {search_count}\n"
            f"Ваш баланс: ${balance:.2f}\n"
            f"Реферальный баланс: ${referral_balance:.2f}\n"
            f"Дата регистрации: {registration_date}\n"
            f"(Вы агент уже: {agent_duration})"
        )
        await callback.message.edit_text(profile_text, reply_markup=profile_keyboard())
        await callback.answer("Профиль обновлён ?")
    # ---------- Пополнение ----------
    elif data == "top_up":
        balance += 100
        await state.update_data(balance=balance)
        await callback.answer("Баланс пополнен на 100 $ ?", show_alert=True)
    # ---------- Купить запросы ----------
    elif data == "buy_requests":
        search_count += 1
        await state.update_data(search_count=search_count)
        await callback.answer("Вы купили 1 запрос ?", show_alert=True)
    else:
        await callback.answer(f"Вы нажали: {data}", show_alert=True)

# ------------------ MAIN ------------------

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
