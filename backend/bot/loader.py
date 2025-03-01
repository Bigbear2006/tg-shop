import logging

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import MemoryStorage

from bot.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format='[{asctime}] {levelname} {name}: {message}',
    datefmt='%Y-%m-%d %H:%M:%S',
    style='{',
)
logger = logging.getLogger('bot')

bot = Bot(settings.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
