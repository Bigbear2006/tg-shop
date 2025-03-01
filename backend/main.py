import asyncio
import os

import django
import openpyxl
from aiogram.types import BotCommand

from bot.loader import bot, dp, logger


def init_excel():
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = 'Заказы'
    sheet.append([
        'ID пользователя',
        'Имя пользователя',
        'Адрес доставки',
        'ID товара',
        'Товар',
        'Количество',
        'Сумма',
        'Дата заказа'
    ])
    wb.save('orders.xlsx')


async def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    django.setup()

    init_excel()

    from bot.handlers import commands, catalog, cart
    dp.include_routers(commands.router, catalog.router, cart.router)
    logger.info('Starting bot...')

    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands([
        BotCommand(command='/catalog', description='Каталог'),
        BotCommand(command='/cart', description='Корзина'),
    ])
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
