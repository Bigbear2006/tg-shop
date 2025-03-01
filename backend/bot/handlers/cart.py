import openpyxl
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, \
    InputMediaPhoto, LabeledPrice, PreCheckoutQuery

from bot.filters import IsChatMember
from bot.keyboards.utils import keyboard_from_queryset
from bot.loader import logger
from bot.settings import settings
from bot.states import CatalogState
from shop.models import Product

router = Router()
router.message.filter(IsChatMember())


@router.message(Command('cart'))
@router.message(F.text == 'Корзина')
async def display_cart(msg: Message, state: FSMContext):
    await state.update_data({'product_message': None})
    cart = await state.get_value('cart', {})

    if not cart:
        return await msg.answer('Ваша корзина пуста. Перейти в каталог - /catalog')

    products = Product.objects.filter(pk__in=cart.keys())
    await msg.answer(
        'Ваша корзина',
        reply_markup=await keyboard_from_queryset(
            products,
            prefix='cart_product'
        )
    )


@router.callback_query(F.data.startswith('cart_product'))
async def display_cart_product(query: CallbackQuery, state: FSMContext):
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
        [InlineKeyboardButton(text='Купить', callback_data=f'buy_{product_id}')],
        [InlineKeyboardButton(text='Сменить количество', callback_data=f'change_count_{product_id}')],
        [InlineKeyboardButton(text='Удалить из корзины', callback_data=f'delete_from_cart_{product_id}')],
    ])

    product_message: Message = await state.get_value('product_message')
    if product_message:
        product_message = await product_message.edit_media(
            InputMediaPhoto(media=media, caption=caption),
        )
    else:
        product_message = await query.message.reply_photo(
            media,
            caption=caption,
            reply_markup=kb,
        )
    await state.update_data({'product_message': product_message})

    if not product.image_tg_id:
        product.image_tg_id = product_message.photo[0].file_id
        await product.asave()


@router.callback_query(F.data.startswith('buy'))
async def buy_product(query: CallbackQuery, state: FSMContext):
    try:
        product_id = int(query.data.split('_')[-1])
    except Exception as e:
        return logger.exception(
            f'An exception occurred '
            f'during the extracting product_id from {query.data}: {e}'
        )

    await state.update_data(product_id=product_id)
    await state.set_state(CatalogState.delivery_location)

    await query.message.answer('Введите адрес для доставки')


@router.message(StateFilter(CatalogState.delivery_location))
async def set_delivery_location(msg: Message, state: FSMContext):
    await state.update_data(delivery_location=msg.text)
    data = await state.get_data()
    product_id = data.get('product_id', 3)
    cart = data.get('cart', {3: 5})

    product = await Product.objects.aget(pk=product_id)
    product_count = cart.get(product_id)
    amount = int(product.price * 100) * product_count

    await state.set_state(None)
    await msg.bot.send_invoice(
        msg.chat.id,
        'Покупка',
        f'Покупка {product.title} ({product_count} шт.)',
        f'product_{product_id}',
        settings.CURRENCY,
        [LabeledPrice(label=settings.CURRENCY, amount=amount)],
        provider_token=settings.PROVIDER_TOKEN,
    )


@router.pre_checkout_query()
async def accept_pre_checkout_query(query: PreCheckoutQuery):
    await query.answer(True)


@router.message(F.successful_payment)
async def on_successful_payment(msg: Message, state: FSMContext):
    print(msg.successful_payment)
    data = await state.get_data()
    await msg.answer(f'Поздравляем! Вы оплатили {msg.successful_payment.total_amount}')
    openpyxl.load_workbook('orders.xlsx')


@router.callback_query(F.data.startswith('change_count'))
async def change_product_count(query: CallbackQuery, state: FSMContext):
    try:
        product_id = int(query.data.split('_')[-1])
    except Exception as e:
        return logger.exception(
            f'An exception occurred '
            f'during the extracting product_id from {query.data}: {e}'
        )

    await state.update_data({'product_id': product_id})
    await state.set_state(CatalogState.count)
    await query.message.answer('Укажите количество')


@router.callback_query(F.data.startswith('delete_from_cart'))
async def display_cart_product(query: CallbackQuery, state: FSMContext):
    try:
        product_id = int(query.data.split('_')[-1])
    except Exception as e:
        return logger.exception(
            f'An exception occurred '
            f'during the extracting product_id from {query.data}: {e}'
        )

    cart: dict[int, int] = await state.get_value('cart', {})
    cart.pop(product_id, None)
    await state.update_data({'cart': cart})

    product = await Product.objects.aget(pk=product_id)
    await query.message.answer(f'Товар {product.title} удален из корзины')
