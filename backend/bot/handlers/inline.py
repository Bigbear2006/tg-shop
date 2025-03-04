import difflib
import hashlib

from aiogram import Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from bot.filters import IsChatMember
from bot.settings.faq import FAQ

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
