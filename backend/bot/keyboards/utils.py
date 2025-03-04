from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from django.db.models import Model, QuerySet

from bot.settings import settings
from shop.models import Category, Product


async def get_pagination_buttons(
    previous_button_data: str = None,
    next_button_data: str = None,
) -> list[InlineKeyboardButton]:
    pagination_buttons = []

    if previous_button_data:
        pagination_buttons.append(
            InlineKeyboardButton(
                text='<<',
                callback_data=previous_button_data,
            ),
        )

    if next_button_data:
        pagination_buttons.append(
            InlineKeyboardButton(text='>>', callback_data=next_button_data),
        )

    return pagination_buttons


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

    kb.adjust(1)
    kb.row(*await get_pagination_buttons(
        previous_button_data,
        next_button_data,
    ))
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
    return (
        f'category_{category.parent_category.pk}'
        if category.parent_category
        else 'categories_root'
    )


async def get_categories_root_keyboard(page: int = 1) -> InlineKeyboardMarkup:
    return await get_paginated_keyboard(
        Category,
        filters={'parent_category': None},
        page=page,
        prefix='category',
    )


async def get_categories_keyboard(
    parent_category: Category,
    page: int = 1,
) -> InlineKeyboardMarkup:
    return await get_paginated_keyboard(
        Category,
        filters={'parent_category': parent_category},
        page=page,
        prefix='category',
        back_button_data=get_back_button_data(parent_category),
    )


async def get_products_keyboard(
    category: Category,
    page: int = 1,
) -> InlineKeyboardMarkup:
    return await get_paginated_keyboard(
        Product,
        filters={'category': category},
        page=page,
        prefix='product',
        back_button_data=get_back_button_data(category),
    )


async def get_product_keyboard(product_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='Добавить в корзину',
                    callback_data=f'add_to_cart_{product_id}',
                ),
            ],
        ],
    )


async def get_product_detail_keyboard(product_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='Купить',
                    callback_data=f'buy_{product_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    text='Сменить количество',
                    callback_data=f'change_count_{product_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    text='Удалить из корзины',
                    callback_data=f'delete_from_cart_{product_id}',
                ),
            ],
        ],
    )


async def get_cart_keyboard(
        cart: dict[str, int],
        page: int = 1,
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    total_count = len(cart)
    total_pages = (total_count + settings.PAGE_SIZE - 1) // settings.PAGE_SIZE
    start, end = (page - 1) * settings.PAGE_SIZE, page * settings.PAGE_SIZE
    products = Product.objects.filter(pk__in=cart.keys())[start:end]

    kb.button(text='Оплатить всю корзину', callback_data='buy_whole_cart')
    async for product in products:
        kb.button(
            text=f'{product.title} ({cart.get(str(product.pk), 0)} шт.)',
            callback_data=f'cart_product_{product.pk}',
        )

    kb.adjust(1)
    kb.row(*await get_pagination_buttons(
        'cart_previous' if page > 1 else None,
        'cart_next' if page < total_pages else None,
    ))
    return kb.as_markup()
