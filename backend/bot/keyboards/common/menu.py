from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Каталог')],
        [KeyboardButton(text='Корзина')],
    ],
    resize_keyboard=True,
)
