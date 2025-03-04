from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.filters import IsChatMember
from bot.keyboards.reply import menu_kb
from bot.loader import logger
from shop.models import Client

router = Router()


@router.message(Command('start'), IsChatMember())
async def start(msg: Message, state: FSMContext):
    client, created = await Client.objects.create_or_update_from_tg_user(
        msg.from_user,
    )
    if created:
        logger.info(f'New client {client} id={client.pk} was created')
    else:
        logger.info(f'Client {client} id={client.pk} was updated')

    await state.set_state(None)
    return await msg.answer(
        f'Привет, {msg.from_user.full_name}!\n'
        f'Перейти в каталог - /catalog\n\n'
        f'Если у тебя есть вопрос, то ты можешь задать его, например:\n'
        f'@learnpoemsbot как оформить заказ?',
        reply_markup=menu_kb,
    )
