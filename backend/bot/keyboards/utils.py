from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from django.db.models import QuerySet, Model

from bot.settings import settings
from shop.models import Product, Category


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


async def get_paginated_keyboard(
        model: type[Model],
        *,
        filters: dict = None,
        page: int = 1,
        prefix: str = '',
        back_button_data: str = None,
        previous_button_data: str = 'catalog_previous',
        next_button_data: str = 'catalog_next',
) -> InlineKeyboardMarkup:
    if not filters:
        filters = {}

    total_count = await model.objects.filter(**filters).acount()
    total_pages = (total_count + settings.PAGE_SIZE - 1) // settings.PAGE_SIZE
    start, end = (page - 1) * settings.PAGE_SIZE, page * settings.PAGE_SIZE
    queryset = model.objects.filter(**filters)[start:end]

    return await keyboard_from_queryset(
        queryset,
        prefix=prefix,
        back_button_data=back_button_data,
        previous_button_data=previous_button_data if page > 1 else None,
        next_button_data=next_button_data if page < total_pages else None,
    )


def get_back_button_data(category: Category) -> str:
    return f'category_{category.parent_category.pk}' if category.parent_category else 'categories_root'


async def get_categories_root_keyboard(page: int = 1) -> InlineKeyboardMarkup:
    return await get_paginated_keyboard(
        Category,
        filters={'parent_category': None},
        page=page,
        prefix='category',
    )


async def get_categories_keyboard(parent_category: Category, page: int = 1) -> InlineKeyboardMarkup:
    return await get_paginated_keyboard(
        Category,
        filters={'parent_category': parent_category},
        page=page,
        prefix='category',
        back_button_data=get_back_button_data(parent_category)
    )


async def get_products_keyboard(category: Category, page: int = 1) -> InlineKeyboardMarkup:
    return await get_paginated_keyboard(
        Product,
        filters={'category': category},
        page=page,
        prefix='product',
        back_button_data=get_back_button_data(category)
    )
