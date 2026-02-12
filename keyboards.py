from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def bottom_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📂 Показать меню"), KeyboardButton(text="👤 Выбрать пользователя")]],
        resize_keyboard=True
    )

def start_inline_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Поиск по неполным данным", callback_data="partial_search")],
            [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")],
            [InlineKeyboardButton(text="🤖 Мои боты", callback_data="my_bots")],
            [InlineKeyboardButton(text="🤝 Партнёрская программа", callback_data="partner_program")],
        ]
    )﻿
