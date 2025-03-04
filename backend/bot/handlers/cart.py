import threading
from datetime import datetime

import openpyxl
from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)

from bot.filters import IsChatMember
from bot.handlers.utils import send_or_update_product_message, add_order
from bot.keyboards.utils import get_cart_keyboard, get_product_detail_keyboard
from bot.loader import logger
from bot.settings import settings
from bot.states import CatalogState
from shop.models import Product

router = Router()
router.message.filter(IsChatMember())


@router.message(Command('cart'))
@router.message(F.text == 'Корзина')
async def display_cart(msg: Message, state: FSMContext):
    await state.update_data(product_message_id=None, page=1)
    cart = await state.get_value('cart', {})

    if not cart:
        await msg.answer(
            'Ваша корзина пуста.\n'
            'Перейти в каталог - /catalog',
        )
        return

    message = await msg.answer(
        'Ваша корзина',
        reply_markup=await get_cart_keyboard(cart),
    )
    await state.update_data(cart_message_id=message.message_id)


@router.callback_query(F.data.in_(('cart_previous', 'cart_next')))
async def change_cart_page(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cart = data.get('cart', {})
    page = data.get('page', 1)

    if query.data == 'cart_previous':
        page -= 1
    else:
        page += 1
    await state.update_data(page=page)

    await query.message.edit_reply_markup(
        reply_markup=await get_cart_keyboard(cart, page)
    )


@router.callback_query(F.data.startswith('cart_product'))
async def display_cart_product(query: CallbackQuery, state: FSMContext):
    await send_or_update_product_message(
        query,
        state,
        reply_markup=await get_product_detail_keyboard(
            int(query.data.split('_')[-1]),
        ),
    )


@router.callback_query(F.data.startswith('buy'))
async def buy(query: CallbackQuery, state: FSMContext):
    if not query.data == 'buy_whole_cart':
        product_id = int(query.data.split('_')[-1])
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
    test_card_info = (
        'Для оплаты используйте данные тестовой карты: '
        '1111 1111 1111 1026, 12/22, 000'
    )

    if buy_whole_cart:
        amount = sum(
            [
                int(product.price * 100) * cart.get(str(product.pk))
                async for product in Product.objects.filter(pk__in=cart.keys())
            ],
        )

        if amount > settings.MAX_AMOUNT:
            await msg.answer(
                'Сумма покупки превышает 250 000 ₽.\n.'
                'Попробуйте оплатить товары отдельно.'
            )
            return

        await state.set_state(None)
        await msg.bot.send_invoice(
            msg.chat.id,
            'Покупка',
            f'Покупка всей корзины.\n{test_card_info}',
            'whole_cart',
            settings.CURRENCY,
            [LabeledPrice(label=settings.CURRENCY, amount=amount)],
            provider_token=settings.PROVIDER_TOKEN,
        )
        return

    product_id = data.get('product_id')
    product = await Product.objects.aget(pk=product_id)
    product_count = cart.get(str(product_id))
    amount = int(product.price * 100) * product_count

    if amount > settings.MAX_AMOUNT:
        await msg.answer(
            'Сумма покупки превышает 250 000 ₽.\n'
            'Попробуйте уменьшить количество товара'
        )
        return

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

    file_lock = threading.Lock()
    with file_lock:
        wb = openpyxl.load_workbook(settings.ORDERS_FILE)
        sheet = wb.active

        if msg.successful_payment.invoice_payload == 'whole_cart':
            async for product in Product.objects.filter(pk__in=cart.keys()):
                product_count = cart.get(str(product.pk))
                add_order(
                    sheet,
                    msg,
                    product=product,
                    product_count=product_count,
                    amount=f'{(product.price * product_count):.2f}',
                    delivery_location=delivery_location,
                    order_date=order_date,
                )
            wb.save(settings.ORDERS_FILE)

            await state.update_data(buy_whole_cart=None)
            await msg.answer(
                f'Поздравляем c покупкой '
                f'на сумму {msg.successful_payment.total_amount / 100:.2f} ₽!',
            )
        else:
            product = await Product.objects.aget(
                pk=int(msg.successful_payment.invoice_payload.split('_')[-1]),
            )
            product_count = cart.get(str(product.pk))
            add_order(
                sheet,
                msg,
                product=product,
                product_count=product_count,
                amount=f'{msg.successful_payment.total_amount / 100:.2f}',
                delivery_location=delivery_location,
                order_date=order_date,
            )
            wb.save(settings.ORDERS_FILE)

            await msg.answer(
                f'Поздравляем c покупкой {product.title} ({product_count} шт.) '
                f'на сумму {msg.successful_payment.total_amount / 100:.2f} ₽!',
            )


@router.callback_query(F.data.startswith('change_count'))
async def change_product_count(query: CallbackQuery, state: FSMContext):
    await state.update_data(product_id=int(query.data.split('_')[-1]))
    await state.set_state(CatalogState.count)
    await query.message.answer('Укажите количество')


@router.callback_query(F.data.startswith('delete_from_cart'))
async def delete_product_from_cart(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cart = data.get('cart', {})
    cart_message_id = data.get('cart_message_id')

    product_id = query.data.split('_')[-1]
    cart.pop(product_id, None)

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

    await state.update_data(cart=cart, product_message_id=None, page=1)
    await query.message.delete()
