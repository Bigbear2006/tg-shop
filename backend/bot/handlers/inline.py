import difflib
import hashlib

from aiogram import Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from bot.filters import IsChatMember

FAQ = {
    'как оформить заказ?':
        'Выберите товар, добавьте в корзину и нажмите «Оформить заказ».',
    'какие способы оплаты доступны?':
        'Мы принимаем карты, PayPal и оплату при получении.',
    'сколько времени занимает доставка?':
        'Доставка занимает от 1 до 5 дней в зависимости от региона.',
    'как отследить заказ?':
        'После отправки вы получите трек-номер для отслеживания.',
    'можно ли вернуть товар?':
        'Да, у вас есть 14 дней на возврат товара без объяснения причин.',
    'что делать, если товар пришел с браком?':
        'Свяжитесь с поддержкой, и мы заменим товар или вернем деньги.',
    'есть ли гарантия на товары?':
        'На все товары действует гарантия от 6 до 24 месяцев.',
    'как связаться с поддержкой?':
        'Вы можете написать в чат-боте или позвонить по номеру '
        '+7 (900) 123-45-67.',
    'какие бренды представлены в магазине?':
        'У нас есть Apple, Samsung, Xiaomi, Sony и многие другие.',
    'где можно посмотреть характеристики товаров?':
        'Каждый товар имеет подробное описание на сайте и в боте.',
}

router = Router()
router.message.filter(IsChatMember())


@router.inline_query()
async def inline_faq(query: InlineQuery):
    questions: list[str] = difflib.get_close_matches(
        query.query.lower(),
        FAQ.keys(),
        cutoff=0.2,
    )

    results = []
    for q in questions:
        answer = FAQ.get(q)
        results.append(
            InlineQueryResultArticle(
                id=hashlib.md5(q.encode()).hexdigest(),
                title=q.title(),
                description=(
                    f'{answer[:50]}...' if len(answer) > 50 else answer
                ),
                input_message_content=InputTextMessageContent(
                    message_text=f'{q.title()}\n\n{answer}',
                ),
            ),
        )

    await query.answer(results, cache_time=1)
