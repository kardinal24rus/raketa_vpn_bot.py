from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from keyboards import start_inline_keyboard, get_partial_search_keyboard
from states import SearchState

router = Router()

START_TEXT = (
    "🕵️ Личность:\n"
    "Петросян ЕвгенийАнатольевич 04.06.1976 – ФИО\n\n"
    "📲 Контакты:\n79999688666 – номер телефона\n79999688666@mail.ru – email\n\n"
    "🚘 Транспорт:\nВ395ОК199 – номер автомобиля\nXTA211440C5106924 – VIN автомобиля\n\n"
    "💬 Социальные сети:\nvk.com/sherpik – Вконтакте\tiiktok.com/@shepps – Tiiktok\ninstagram.com/mizim – Instagram\nok.ru/profile/58460 – Одноклассники\n\n"
    "📟 Telegram:\n@glazik, tg123456 – логин или ID\n\n"
    "📄 Документы:\n/vu 1234567890 – водительские права\n/passport 1234567890 – паспорт\n/snils 12345678901 – СНИЛС\n/inn 2540214547 – ИНН\n\n"
    "🌐 Онлайн-следы:\n/tag хирург москва – поиск по телефонным книгам\nsherlock.com или 1.1.1.1 – домен или IP\n\n"
    "🏚 Недвижимость:\n/adr Москва, Островитянова, 9к4, 94\n77:01:0004042:6987 – кадастровый номер\n\n"
    "🏢 Юридическое лицо:\n/inn 2540214547 – ИНН\n1107449004464 – ОГРН или ОГРНИП\n\n"
    "📸 Отправьте лицо человека, чтобы попробовать найти его."
)

@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.set_state(SearchState.form)
    await message.answer(START_TEXT, reply_markup=start_inline_keyboard())

@router.callback_query(lambda c: c.data == "partial_search")
async def partial_search(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "Вы можете узнать любое количество данных — фамилия, имя, отчество, дату или год рождения, возраст, место рождения и так далее. Достаточно заполнить то, что у вас есть, все поля не обязательны.",
        reply_markup=get_partial_search_keyboard({})
    )
    await callback.answer()