from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    Message,
)
from django.db.models import Count

from bot.filters import IsChatMember
from bot.handlers.utils import send_or_update_product_message
from bot.keyboards.inline import yes_no_kb
from bot.keyboards.utils import (
    get_categories_keyboard,
    get_categories_root_keyboard,
    get_product_keyboard,
    get_products_keyboard,
)
from bot.states import CatalogState
from shop.models import Category, Product

router = Router()
router.message.filter(IsChatMember())


@router.message(Command('catalog'))
@router.message(F.text == 'Каталог')
async def display_catalog(msg: Message, state: FSMContext):
    await state.update_data(product_message_id=None, category_id=None, page=1)
    await msg.answer(
        'Все категории',
        reply_markup=await get_categories_root_keyboard(),
    )


@router.callback_query(F.data.in_(('catalog_previous', 'catalog_next')))
async def change_catalog_page(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('page', 1)
    category_id = data.get('category_id')

    if query.data == 'catalog_previous':
        page -= 1
    else:
        page += 1
    await state.update_data(page=page)

    if not category_id:
        await query.message.edit_text(
            'Все категории',
            reply_markup=await get_categories_root_keyboard(page),
        )
        return

    category = (
        await Category.objects.annotate(
            subcategories_count=Count('subcategories'),
        )
        .select_related('parent_category')
        .aget(pk=category_id)
    )

    if category.subcategories_count == 0:
        await query.message.edit_text(
            f'Товары категории {category}',
            reply_markup=await get_products_keyboard(category, page),
        )
        return

    await query.message.edit_text(
        f'Категория {category}',
        reply_markup=await get_categories_keyboard(category, page),
    )


@router.callback_query(F.data.startswith('category'))
async def expand_category(query: CallbackQuery, state: FSMContext):
    category_id = int(query.data.split('_')[-1])
    await state.update_data(category_id=category_id)
    await state.update_data(page=1)

    category = (
        await Category.objects.annotate(
            subcategories_count=Count('subcategories'),
        )
        .select_related('parent_category')
        .aget(pk=category_id)
    )

    if category.subcategories_count == 0:
        await query.message.edit_text(
            f'Товары категории {category}',
            reply_markup=await get_products_keyboard(category),
        )
        return

    await query.message.edit_text(
        f'Категория {category}',
        reply_markup=await get_categories_keyboard(category),
    )


@router.callback_query(F.data == 'categories_root')
async def display_categories_root(query: CallbackQuery, state: FSMContext):
    await state.update_data(category_id=None)
    await query.message.edit_text(
        'Все категории',
        reply_markup=await get_categories_root_keyboard(),
    )


@router.callback_query(F.data.startswith('product'))
async def display_product(query: CallbackQuery, state: FSMContext):
    await send_or_update_product_message(
        query,
        state,
        reply_markup=await get_product_keyboard(
            int(query.data.split('_')[-1]),
        ),
    )


@router.callback_query(F.data.startswith('add_to_cart'))
async def add_to_cart(query: CallbackQuery, state: FSMContext):
    product = await Product.objects.aget(pk=int(query.data.split('_')[-1]))

    await state.update_data(product_id=product.pk)
    await state.set_state(CatalogState.count)
    await query.message.answer(
        f'Сколько штук {product.title} вы хотите добавить в корзину?',
    )


@router.message(StateFilter(CatalogState.count))
async def set_product_count(msg: Message, state: FSMContext):
    try:
        count = int(msg.text)
    except (ValueError, TypeError):
        await msg.answer(
            'Пожалуйста, введите целое положительное число.',
        )
        return

    if count <= 0:
        await msg.answer(
            'Пожалуйста, введите целое положительное число.',
        )
        return

    product = await Product.objects.aget(
        pk=await state.get_value('product_id'),
    )

    await state.update_data(count=count)
    await state.set_state(CatalogState.confirmation)
    await msg.answer(
        f'Вы точно хотите добавить в корзину {product.title} ({count} шт.)?',
        reply_markup=yes_no_kb,
    )


@router.callback_query(F.data == 'yes', StateFilter(CatalogState.confirmation))
async def confirm_product_addition(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    product_id = data.get('product_id')
    count = data.get('count')
    cart = data.get('cart', {})

    cart.update({product_id: count})
    await state.update_data(cart=cart)

    product = await Product.objects.aget(pk=product_id)
    await state.set_state(None)
    await query.message.answer(
        f'Вы добавили в корзину {product.title} ({count} шт.)\n'
        f'Перейти в корзину - /cart',
    )


@router.callback_query(F.data == 'no', StateFilter(CatalogState.confirmation))
async def cancel_product_addition(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    product_id = data.get('product_id')
    count = data.get('count')

    product = await Product.objects.aget(pk=product_id)
    await state.set_state(None)
    await query.message.answer(
        f'Добавление в корзину товара {product.title} ({count} шт.) отменено\n'
        f'Перейти в корзину - /cart',
    )
