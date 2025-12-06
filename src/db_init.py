import logging

from tortoise import Tortoise
from settings import Settings


logger = logging.getLogger(__name__)
settings = Settings()


async def init():
    db_url = (
        f'postgres://{settings.db_user}:{settings.db_password}'
        f'@{settings.db_host}:{settings.db_port}/{settings.db_name}'
    )
    logger.info('initializing database connection')
    await Tortoise.init(db_url=db_url, modules={'models': ['src.crud.models']})
    await Tortoise.generate_schemas()
    logger.info('database schemas generated')


async def on_shutdown():
    logger.info('closing database connections')
    await Tortoise.close_connections()
