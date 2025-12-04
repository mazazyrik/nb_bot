import asyncio
import logging

from aiogram import Dispatcher
from aiogram.enums import ParseMode

from settings import Settings
from src.bot import init_bot
from src.db_init import init as init_database_session
from src.db_init import on_shutdown as close_db_session


logger = logging.getLogger(__name__)


async def startup():
    settings_config = Settings()
    settings_config._get_parse_mode()
    await init_database_session()
    parse_mode = ParseMode[settings_config.parse_mode]
    bot = await init_bot(settings_config.bot_token, parse_mode)
    dp = Dispatcher()
    logger.info('starting bot polling')
    try:
        await dp.start_polling(bot)
    finally:
        logger.info('shutting down services')
        await close_db_session()
        await bot.session.close()


def run():
    logging.basicConfig(level=logging.INFO)
    asyncio.run(startup())


if __name__ == '__main__':
    run()
