import logging

from tortoise import Tortoise
from settings import Settings


logger = logging.getLogger(__name__)
settings = Settings()


async def init():
    db_url = (
        f'postgres://{settings.postgres_user}:{settings.postgres_password}'
        f'@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}'
    )
    logger.info('initializing database connection')
    await Tortoise.init(db_url=db_url, modules={'models': ['crud.models']})
    await Tortoise.generate_schemas()
    logger.info('database schemas generated')


async def on_shutdown():
    logger.info('closing database connections')
    await Tortoise.close_connections()
