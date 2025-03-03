from typing import Any

from aiogram.enums import ChatMemberStatus
from aiogram.filters import BaseFilter
from aiogram.types import Message

from bot.keyboards.inline import subscribe_chats_kb
from bot.settings import settings


class IsChatMember(BaseFilter):
    async def __call__(self, msg: Message) -> bool | dict[str, Any]:
        for chat_id in settings.SUBSCRIBE_CHATS:
            member = await msg.bot.get_chat_member(chat_id, msg.from_user.id)
            if member.status in (
                ChatMemberStatus.LEFT,
                ChatMemberStatus.KICKED,
            ):
                await msg.answer(
                    f'Привет, {msg.from_user.full_name}!\n'
                    f'Чтобы использовать бота '
                    f'надо подписаться на наш канал и чат',
                    reply_markup=subscribe_chats_kb,
                )
                return False
        return True
