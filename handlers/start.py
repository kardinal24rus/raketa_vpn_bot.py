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
    await message.answer("Выберите язык / Choose language:", reply_markup=kb)