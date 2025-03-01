from typing import Any, Union, Dict

from aiogram.enums import ChatMemberStatus
from aiogram.filters import BaseFilter
from aiogram.types import Message

from bot.settings import settings


class IsChatMember(BaseFilter):
    async def __call__(self, msg: Message) -> Union[bool, Dict[str, Any]]:
        for chat_id in settings.SUBSCRIBE_CHATS:
            member = await msg.bot.get_chat_member(chat_id, msg.from_user.id)
            if member.status in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED):
                await msg.answer(
                    f'Привет, {msg.from_user.full_name}!\n'
                    f'Чтобы использовать бота надо подписаться на канал.'
                )
                return False

        return True
