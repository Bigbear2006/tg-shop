from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.filters import IsChatMember
from bot.keyboards.common import menu_kb
router = Router()


@router.message(Command('start'), IsChatMember())
async def start(msg: Message, state: FSMContext):
    await state.clear()
    return await msg.answer(
        f'Привет, {msg.from_user.full_name}!',
        reply_markup=menu_kb
    )
