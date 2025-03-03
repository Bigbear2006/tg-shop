from dataclasses import dataclass, field

from environs import Env

env = Env()
env.read_env()


@dataclass
class Settings:
    BOT_TOKEN: str = field(default_factory=lambda: env('BOT_TOKEN'))
    PROVIDER_TOKEN: str = field(default_factory=lambda: env('PROVIDER_TOKEN'))
    REDIS_URL: str = field(default_factory=lambda: env('REDIS_URL'))

    CURRENCY: str = field(default='RUB')
    PAGE_SIZE: int = field(default=1)
    ORDERS_FILE: str = field(default='orders.xlsx')
    SUBSCRIBE_CHATS: list = field(default_factory=lambda: ['-1001708499155'])
