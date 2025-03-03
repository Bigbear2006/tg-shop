from datetime import datetime

import openpyxl
from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, \
    InputMediaPhoto, LabeledPrice, PreCheckoutQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.filters import IsChatMember
from bot.loader import logger
from bot.settings import settings
from bot.states import CatalogState
from shop.models import Product

router = Router()
router.message.filter(IsChatMember())


async def get_cart_keyboard(cart: dict[str, int]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    products = Product.objects.filter(pk__in=cart.keys())

    kb.button(text='Оплатить всю корзину', callback_data='buy_whole_cart')
    async for product in products:
        kb.button(
            text=f'{product.title} ({cart.get(str(product.pk), 0)} шт.)',
            callback_data=f'cart_product_{product.pk}',
        )
    kb.adjust(1)
    return kb.as_markup()


@router.message(Command('cart'))
@router.message(F.text == 'Корзина')
async def display_cart(msg: Message, state: FSMContext):
    await state.update_data(product_message_id=None)
    cart = await state.get_value('cart', {})

    if not cart:
        return await msg.answer('Ваша корзина пуста.\nПерейти в каталог - /catalog')

    # kb = InlineKeyboardBuilder()
    # products = Product.objects.filter(pk__in=cart.keys())
    #
    # kb.button(text='Оплатить всю корзину', callback_data='buy_whole_cart')
    # async for product in products:
    #     kb.button(
    #         text=f'{product.title} ({cart.get(str(product.pk), 0)} шт.)',
    #         callback_data=f'cart_product_{product.pk}',
    #     )
    # kb.adjust(1)

    message = await msg.answer(
        'Ваша корзина',
        reply_markup=await get_cart_keyboard(cart),
    )
    await state.update_data(cart_message_id=message.message_id)


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
        except TelegramBadRequest as e:
            return logger.exception(e)
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


@router.callback_query(F.data.startswith('buy'))
async def buy(query: CallbackQuery, state: FSMContext):
    if not query.data == 'buy_whole_cart':
        try:
            product_id = int(query.data.split('_')[-1])
        except Exception as e:
            return logger.exception(
                f'An exception occurred '
                f'during the extracting product_id from {query.data}: {e}'
            )
        await state.update_data(product_id=product_id)
    else:
        await state.update_data(buy_whole_cart=True)

    await state.set_state(CatalogState.delivery_location)
    await query.message.answer('Введите адрес для доставки')


@router.message(StateFilter(CatalogState.delivery_location))
async def set_delivery_location(msg: Message, state: FSMContext):
    await state.update_data(delivery_location=msg.text)
    data = await state.get_data()
    cart = data.get('cart')
    buy_whole_cart = data.get('buy_whole_cart')
    test_card_info = 'Для оплаты используйте данные тестовой карты: 1111 1111 1111 1026, 12/22, 000'

    if buy_whole_cart:
        amount = sum([
            int(product.price * 100) * cart.get(str(product.pk))
            async for product in Product.objects.filter(pk__in=cart.keys())
        ])
        await state.set_state(None)
        return await msg.bot.send_invoice(
            msg.chat.id,
            'Покупка',
            f'Покупка всей корзины.\n{test_card_info}',
            f'whole_cart',
            settings.CURRENCY,
            [LabeledPrice(label=settings.CURRENCY, amount=amount)],
            provider_token=settings.PROVIDER_TOKEN,
        )

    product_id = data.get('product_id')
    product = await Product.objects.aget(pk=product_id)
    product_count = cart.get(str(product_id))
    amount = int(product.price * 100) * product_count

    await state.set_state(None)
    await msg.bot.send_invoice(
        msg.chat.id,
        'Покупка',
        f'Покупка {product.title} ({product_count} шт.).\n{test_card_info}',
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
    logger.info(f'Successful payment: {msg.successful_payment}')

    data = await state.get_data()
    cart = data.get('cart')
    delivery_location = data.get('delivery_location')
    order_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    wb = openpyxl.load_workbook(settings.ORDERS_FILE)
    sheet = wb.active

    if msg.successful_payment.invoice_payload == 'whole_cart':
        async for product in Product.objects.filter(pk__in=cart.keys()):
            product_count = cart.get(str(product.pk))
            sheet.append([
                msg.successful_payment.provider_payment_charge_id,
                msg.from_user.id,
                product.pk,
                f'@{msg.from_user.username}',
                delivery_location,
                product.title,
                product_count,
                f'{(product.price * product_count):.2f}',
                order_date,
            ])
        wb.save(settings.ORDERS_FILE)

        await state.update_data(buy_whole_cart=None)
        await msg.answer(
            f'Поздравляем c покупкой '
            f'на сумму {msg.successful_payment.total_amount / 100:.2f} ₽!'
        )
    else:
        product = await Product.objects.aget(
            pk=int(msg.successful_payment.invoice_payload.split('_')[-1]),
        )
        product_count = cart.get(str(product.pk))
        sheet.append([
            msg.successful_payment.provider_payment_charge_id,
            msg.from_user.id,
            product.pk,
            f'@{msg.from_user.username}',
            delivery_location,
            product.title,
            product_count,
            f'{msg.successful_payment.total_amount / 100:.2f}',
            order_date,
        ])
        wb.save(settings.ORDERS_FILE)
        await msg.answer(
            f'Поздравляем c покупкой {product.title} ({product_count} шт.) '
            f'на сумму {msg.successful_payment.total_amount / 100:.2f} ₽!'
        )


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
async def delete_product_from_cart(query: CallbackQuery, state: FSMContext):
    try:
        product_id = int(query.data.split('_')[-1])
    except Exception as e:
        return logger.exception(
            f'An exception occurred '
            f'during the extracting product_id from {query.data}: {e}'
        )

    data = await state.get_data()
    cart = data.get('cart', {})
    cart_message_id = data.get('cart_message_id')

    cart.pop(str(product_id), None)
    await state.update_data({'cart': cart})

    if len(cart) == 0:
        await query.bot.edit_message_text(
            'Ваша корзина пуста.\nПерейти в каталог - /catalog',
            business_connection_id=query.message.business_connection_id,
            chat_id=query.message.chat.id,
            message_id=cart_message_id,
        )
    else:
        await query.bot.edit_message_reply_markup(
            business_connection_id=query.message.business_connection_id,
            chat_id=query.message.chat.id,
            message_id=cart_message_id,
            reply_markup=await get_cart_keyboard(cart),
        )

    await state.update_data(product_message_id=None)
    await query.message.delete()
