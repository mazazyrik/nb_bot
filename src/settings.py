import logging

from aiogram.enums import ParseMode
from pydantic_settings import BaseSettings
from pydantic import Field

from exceptions import EnvVarNotFoundException


logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    bot_token: str = Field(..., env='BOT_TOKEN')
    members_file_name: str = Field(..., env='MEMBERS_JSON_NAME')
    parse_mode: str = Field(..., env='PARSE_MODE')

    db_user: str = Field(..., env='DB_USER')
    db_password: str = Field(..., env='DB_PASSWORD')
    db_host: str = Field(..., env='DB_HOST')
    db_port: int = Field(..., env='DB_PORT')
    db_name: str = Field(..., env='DB_NAME')

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

    def _get_parse_mode(self):
        if self.parse_mode not in ParseMode.__members__:
            raise EnvVarNotFoundException('PARSE_MODE') 
            # харкод, тк не добраться до атрибута 
    