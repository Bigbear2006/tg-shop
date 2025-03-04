from aiogram import Router
from aiogram.types import ErrorEvent

from bot.loader import logger

router = Router()


@router.errors()
async def error_handler(event: ErrorEvent):
    logger.exception(
        f'{event.exception.__class__.__name__}: '
        f'{str(event.exception)}',
    )
