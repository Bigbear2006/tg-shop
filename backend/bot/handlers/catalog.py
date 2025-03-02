from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, FSInputFile, InlineKeyboardButton, \
    InputMediaPhoto
from asgiref.sync import sync_to_async

from bot.filters import IsChatMember
from bot.keyboards.utils import keyboard_from_queryset
from bot.loader import logger
from bot.settings import settings
from bot.states import CatalogState
from shop.models import Category, Product

router = Router()
router.message.filter(IsChatMember())


@router.message(Command('catalog'))
@router.message(F.text == 'Каталог')
async def display_catalog(msg: Message, state: FSMContext):
    page = 1
    total_count = await Category.objects.acount()
    total_pages = (total_count + settings.PAGE_SIZE - 1) // settings.PAGE_SIZE
    categories = Category.objects.filter(parent_category=None)[:settings.PAGE_SIZE]

    await msg.answer(
        'Все категории',
        reply_markup=await keyboard_from_queryset(
            categories,
            prefix='category',
            previous_button_data='previous_category' if page > 1 else None,
            next_button_data='next_category' if page < total_pages else None,
        )
    )


@router.callback_query(F.data.in_(('previous_category', 'next_category')))
async def category_previous_page(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get('page', 1)
    category_id = data.get('category_id')

    if query.data == 'previous_category':
        page -= 1
    else:
        page += 1
    await state.update_data(page=page)
    print('page and category_id = ', page, category_id)

    total_count = await Category.objects.filter(parent_category=category_id).acount()
    total_pages = (total_count + settings.PAGE_SIZE - 1) // settings.PAGE_SIZE

    start, end = (page - 1) * settings.PAGE_SIZE, page * settings.PAGE_SIZE
    subcategories = Category.objects.filter(parent_category=category_id)[start:end]
    await sync_to_async(subcategories._fetch_all)()

    if not category_id:
        return await query.message.edit_text(
            f'Все категории',
            reply_markup=await keyboard_from_queryset(
                subcategories,
                prefix='category',
                previous_button_data='previous_category' if page > 1 else None,
                next_button_data='next_category' if page < total_pages else None,
            )
        )

    category = await Category.objects.prefetch_related('parent_category').aget(pk=category_id)

    if not subcategories:
        total_count = await Product.objects.filter(category=category).acount()
        total_pages = (total_count + settings.PAGE_SIZE - 1) // settings.PAGE_SIZE
        start, end = (page - 1) * settings.PAGE_SIZE, page * settings.PAGE_SIZE
        products = Product.objects.filter(category=category)[start:end]

        return await query.message.edit_text(
            f'Товары категории {category}',
            reply_markup=await keyboard_from_queryset(
                products,
                prefix='product',
                back_button_data=f'category_{category.parent_category.pk}'
                if category.parent_category else 'categories_root',
                previous_button_data='previous_category' if page > 1 else None,
                next_button_data='next_category' if page < total_pages else None,
            )
        )

    await query.message.edit_text(
        f'Категория {category}',
        reply_markup=await keyboard_from_queryset(
            subcategories,
            prefix='category',
            back_button_data=
            f'category_{category.parent_category.pk}'
            if category.parent_category else 'categories_root',
            previous_button_data='previous_category' if page > 1 else None,
            next_button_data='next_category' if page < total_pages else None,
        )
    )


@router.callback_query(F.data.startswith('category'))
async def expand_category(query: CallbackQuery, state: FSMContext):
    try:
        category_id = int(query.data.split('_')[-1])
    except Exception as e:
        return logger.exception(
            f'An exception occurred '
            f'during the extracting category_id from {query.data}: {e}'
        )
    await state.update_data(category_id=category_id)
    # page = await state.get_value('page', 1)
    page = 1
    await state.update_data(page=page)

    total_count = await Category.objects.filter(parent_category=category_id).acount()
    total_pages = (total_count + settings.PAGE_SIZE - 1) // settings.PAGE_SIZE
    start, end = (page - 1) * settings.PAGE_SIZE, page * settings.PAGE_SIZE

    category = await Category.objects.prefetch_related('parent_category').aget(pk=category_id)
    subcategories = Category.objects.filter(parent_category_id=category_id)[start:end]
    await sync_to_async(subcategories._fetch_all)()

    if not subcategories:
        total_count = await Product.objects.filter(category=category).acount()
        total_pages = (total_count + settings.PAGE_SIZE - 1) // settings.PAGE_SIZE
        products = Product.objects.filter(category=category)[:settings.PAGE_SIZE]

        return await query.message.edit_text(
            f'Товары категории {category}',
            reply_markup=await keyboard_from_queryset(
                products,
                prefix='product',
                back_button_data=f'category_{category.parent_category.pk}'
                if category.parent_category else 'categories_root',
                next_button_data='next_category' if total_pages > 1 else None,
            )
        )

    await query.message.edit_text(
        f'Категория {category}',
        reply_markup=await keyboard_from_queryset(
            subcategories,
            prefix='category',
            back_button_data=
            f'category_{category.parent_category.pk}'
            if category.parent_category else 'categories_root',
            previous_button_data='previous_category' if page > 1 else None,
            next_button_data='next_category' if page < total_pages else None,
        )
    )


@router.callback_query(F.data == 'categories_root')
async def display_catalog(query: CallbackQuery, state: FSMContext):
    page = 1
    total_count = await Category.objects.acount()
    total_pages = (total_count + settings.PAGE_SIZE - 1) // settings.PAGE_SIZE
    categories = Category.objects.filter(parent_category=None)[:settings.PAGE_SIZE]

    await state.update_data(category_id=None)
    await query.message.edit_text(
        'Все категории',
        reply_markup=await keyboard_from_queryset(
            categories,
            prefix='category',
            previous_button_data='previous_category' if page > 1 else None,
            next_button_data='next_category' if page < total_pages else None,
        )
    )


@router.callback_query(F.data.startswith('product'))
async def display_product(query: CallbackQuery, state: FSMContext):
    try:
        product_id = int(query.data.split('_')[-1])
    except Exception as e:
        return logger.exception(
            f'An exception occurred '
            f'during the extracting product_id from {query.data}: {e}'
        )

    product = await Product.objects.aget(pk=product_id)
    media = product.image_tg_id or FSInputFile(product.image.url.lstrip('/'))
    caption = f'{product.title}\n\n{product.description}'
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Добавить в корзину', callback_data=f'add_to_cart_{product_id}')]
    ])

    product_message_id: int = await state.get_value('product_message_id')
    if product_message_id:
        try:
            product_message = await query.bot.edit_message_media(
                media=InputMediaPhoto(media=media, caption=caption),
                business_connection_id=query.message.business_connection_id,
                chat_id=query.message.chat.id,
                message_id=product_message_id,
                reply_markup=kb
            )
        except TelegramBadRequest:
            return
    else:
        product_message = await query.bot.send_photo(
            chat_id=query.message.chat.id,
            photo=media,
            business_connection_id=query.message.business_connection_id,
            caption=caption,
            reply_markup=kb,
            reply_to_message_id=query.message.message_id
        )
    await state.update_data({'product_message_id': product_message.message_id})

    if not product.image_tg_id:
        product.image_tg_id = product_message.photo[0].file_id
        await product.asave()


@router.callback_query(F.data.startswith('add_to_cart'))
async def add_to_cart(query: CallbackQuery, state: FSMContext):
    try:
        product_id = int(query.data.split('_')[-1])
    except Exception as e:
        return logger.exception(
            f'An exception occurred '
            f'during the extracting product_id from {query.data}: {e}'
        )

    product = await Product.objects.aget(pk=product_id)
    await state.update_data({'product_id': product_id})
    await state.set_state(CatalogState.count)
    await query.message.answer(f'Сколько штук {product.title} вы хотите купить?')


@router.message(StateFilter(CatalogState.count))
async def set_product_count(msg: Message, state: FSMContext):
    try:
        count = int(msg.text)
    except Exception:
        return await msg.answer('Пожалуйста, введите целое положительное число.')

    if count <= 0:
        return await msg.answer('Пожалуйста, введите целое положительное число.')

    data = await state.get_data()
    product_id = data.get('product_id')
    cart = data.get('cart', {})

    cart.update({product_id: count})
    await state.update_data({'cart': cart})

    product = await Product.objects.aget(pk=product_id)
    await state.set_state(None)
    await msg.answer(
        f'Вы добавили в корзину {product.title} ({count} шт.)\n'
        f'Перейти в корзину - /cart'
    )


# @router.message(StateFilter(CatalogState.confirmation))
# async def confirm_product_addition(msg: Message, state: FSMContext):


# @router.callback_query()
# async def default(query: CallbackQuery):
#     print(query.data)
