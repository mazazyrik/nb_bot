import asyncio
import logging

from aiogram import Dispatcher
from aiogram.enums import ParseMode

from handlers.menu import menu_router
from handlers.faq import faq_router
from handlers.whishes import whishes_router
from handlers.registration import registration_router
from handlers.start import start_router
from middlewares.admin_role import AdminRoleMiddleware
from middlewares.check_visitor import Auth
from settings import Settings
from bot import init_bot
from db_init import init as init_database_session
from db_init import on_shutdown as close_db_session


logger = logging.getLogger(__name__)


async def startup():
    # settings
    settings_config = Settings()
    settings_config._get_parse_mode()

    # databse
    await init_database_session()

    # bot
    parse_mode = ParseMode[settings_config.parse_mode]
    bot = await init_bot(settings_config.bot_token, parse_mode)
    dp = Dispatcher()
    dp.message.middleware(Auth())
    dp.callback_query.middleware(Auth())
    dp.message.middleware(AdminRoleMiddleware())
    dp.include_router(start_router)
    dp.include_router(registration_router)
    dp.include_router(menu_router)
    dp.include_router(faq_router)
    dp.include_router(whishes_router)
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
