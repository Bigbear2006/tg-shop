import asyncio
import os

import django
import openpyxl
from aiogram import F
from aiogram.types import BotCommand

from bot.loader import bot, dp, logger
from bot.settings import settings


def init_excel():
    if not os.path.exists(settings.ORDERS_FILE):
        wb = openpyxl.Workbook()
        sheet = wb.active
        sheet.title = 'Заказы'
        sheet.append([
            'ID платежа',
            'ID пользователя',
            'ID товара',
            'Имя пользователя',
            'Адрес доставки',
            'Товар',
            'Количество',
            'Сумма',
            'Дата заказа',
        ])
        wb.save(settings.ORDERS_FILE)
        logger.info(f'Created file {settings.ORDERS_FILE}')
    else:
        logger.info(f'File {settings.ORDERS_FILE} already exists')


async def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    django.setup()

    init_excel()

    from bot.handlers import commands, catalog, cart, inline
    dp.include_routers(commands.router, catalog.router, cart.router, inline.router)
    dp.message.filter(F.chat.type == 'private')

    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands([
        BotCommand(command='/start', description='Запустить бота'),
        BotCommand(command='/catalog', description='Каталог'),
        BotCommand(command='/cart', description='Корзина'),
    ])

    logger.info('Starting bot...')
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
