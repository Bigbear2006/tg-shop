from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.filters import IsChatMember
from bot.keyboards.common import menu_kb
from bot.loader import logger
from shop.models import Client

router = Router()


@router.message(Command('start'), IsChatMember())
async def start(msg: Message, state: FSMContext):
    print(msg.from_user)
    try:
        await Client.objects.aget(pk=msg.from_user.id)
        await Client.objects.filter(pk=msg.from_user.id).aupdate(
            first_name=msg.from_user.first_name,
            last_name=msg.from_user.last_name,
            username=msg.from_user.username,
            is_premium=msg.from_user.is_premium,
        )
    except Client.DoesNotExist:
        client = await Client.objects.acreate(
            id=msg.from_user.id,
            first_name=msg.from_user.first_name,
            last_name=msg.from_user.last_name,
            username=msg.from_user.username,
            is_premium=msg.from_user.is_premium,
        )
        logger.info(
            f'New client was created @{client.username} id={client.pk}',
        )

    await state.clear()
    return await msg.answer(
        f'Привет, {msg.from_user.full_name}!',
        reply_markup=menu_kb,
    )
