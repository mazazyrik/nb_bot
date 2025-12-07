import os
import logging

from aiogram.enums import ParseMode
from pydantic_settings import BaseSettings
from pydantic import Field

from exceptions import EnvVarNotFoundException


logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    _BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
    bot_token: str = Field(..., env='BOT_TOKEN')
    members_json_name: str = Field(..., env='MEMBERS_JSON_NAME')
    parse_mode: str = Field(..., env='PARSE_MODE')

    postgres_user: str = Field(..., env='POSTGRES_USER')
    postgres_password: str = Field(..., env='POSTGRES_PASSWORD')
    postgres_host: str = Field(..., env='POSTGRES_HOST')
    postgres_port: int = Field(..., env='POSTGRES_PORT')
    postgres_db: str = Field(..., env='POSTGRES_DB')

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'ignore'

    def _get_parse_mode(self):
        if self.parse_mode not in ParseMode.__members__:
            raise EnvVarNotFoundException('PARSE_MODE')
            # харкод, тк не добраться до атрибута
