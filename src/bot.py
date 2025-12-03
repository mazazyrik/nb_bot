import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode


logger = logging.getLogger(__name__)


async def init_bot(bot_credentials: str, parse_mode: ParseMode) -> Bot:
    default_bot_properties = DefaultBotProperties(parse_mode=parse_mode)
    bot = Bot(token=bot_credentials, default=default_bot_properties)
    logger.info('bot instance created')
    return bot
