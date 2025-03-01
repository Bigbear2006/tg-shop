from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from django.db.models import QuerySet


async def keyboard_from_queryset(
        queryset: QuerySet,
        *,
        prefix: str,
        back_button_data: str = None,
        previous_button_data: str = None,
        next_button_data: str = None,
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    if back_button_data:
        kb.button(text='Назад', callback_data=back_button_data)

    async for obj in queryset:
        kb.button(text=str(obj), callback_data=f'{prefix}_{obj.pk}')

    pagination_buttons = []
    if previous_button_data:
        pagination_buttons.append(InlineKeyboardButton(text='<<', callback_data=previous_button_data))
    if next_button_data:
        pagination_buttons.append(InlineKeyboardButton(text='>>', callback_data=next_button_data))

    kb.adjust(1)
    kb.row(*pagination_buttons)
    return kb.as_markup()
