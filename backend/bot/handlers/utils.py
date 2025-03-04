from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Message,
)
from openpyxl.worksheet.worksheet import Worksheet

from bot.loader import logger
from shop.models import Product


async def send_or_update_product_message(
        query: CallbackQuery,
        state: FSMContext,
        *,
        reply_markup: InlineKeyboardMarkup = None,
) -> None:
    product = await Product.objects.aget(pk=int(query.data.split('_')[-1]))
    media = product.image_tg_id or FSInputFile(product.image.url.lstrip('/'))
    caption = f'{product}\n\n{product.description}'

    product_message_id: int = await state.get_value('product_message_id')
    if product_message_id:
        try:
            product_message = await query.bot.edit_message_media(
                media=InputMediaPhoto(media=media, caption=caption),
                business_connection_id=query.message.business_connection_id,
                chat_id=query.message.chat.id,
                message_id=product_message_id,
                reply_markup=reply_markup,
            )
        except TelegramBadRequest:
            return
    else:
        product_message = await query.bot.send_photo(
            chat_id=query.message.chat.id,
            photo=media,
            business_connection_id=query.message.business_connection_id,
            caption=caption,
            reply_markup=reply_markup,
            reply_to_message_id=query.message.message_id,
        )
    await state.update_data(product_message_id=product_message.message_id)

    if not product.image_tg_id:
        product.image_tg_id = product_message.photo[0].file_id
        await product.asave()
        logger.info(
            f'image_tg_id={product.image_tg_id} '
            f'was added to product {product.title}',
        )


def add_order(
        sheet: Worksheet,
        msg: Message,
        *,
        product: Product,
        product_count: int,
        amount: str,
        delivery_location: str,
        order_date: str,
) -> None:
    sheet.append(
        [
            msg.successful_payment.provider_payment_charge_id,
            msg.from_user.id,
            product.pk,
            f'@{msg.from_user.username}',
            delivery_location,
            product.title,
            product_count,
            amount,
            order_date,
        ],
    )
