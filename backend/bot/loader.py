import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

from bot.settings import settings

logging.basicConfig(
    format='[{asctime}] {levelname} {name}: {message}',
    datefmt='%Y-%m-%d %H:%M:%S',
    style='{',
)
logger = logging.getLogger('bot')
logger.setLevel(logging.INFO)

bot = Bot(settings.BOT_TOKEN)
storage = RedisStorage.from_url(settings.REDIS_URL)
dp = Dispatcher(storage=storage)
