import asyncio
from string import Template

from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from celery import shared_task
from celery.utils.log import get_task_logger

from bot.loader import bot
from shop.models import Client

task_logger = get_task_logger(__name__)


async def send_message(client: Client, text):
    text = Template(text).safe_substitute(client.to_dict())

    try:
        await bot.send_message(client.pk, text)
    except TelegramRetryAfter as e:
        task_logger.info(
            f'Cannot send a message to user (id={client.pk}) '
            f'because of rate limit',
        )
        await asyncio.sleep(e.retry_after)
        await send_message(client, text)
    except TelegramBadRequest as e:
        task_logger.info(
            f'Cannot send a message to user (id={client.pk}) '
            f'because of an {e.__class__.__name__} error: {str(e)}',
        )


@shared_task
def send_dispatch(text: str):
    async def main():
        await asyncio.wait(
            [
                asyncio.create_task(send_message(client, text))
                async for client in Client.objects.all()
            ],
        )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
