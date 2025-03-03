from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

subscribe_chats_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text='Канал',
                url='https://t.me/electronics_shop_channel',
            ),
            InlineKeyboardButton(
                text='Чат',
                url='https://t.me/+uX45AJ1N-0M2MGVi',
            ),
        ],
    ],
)
