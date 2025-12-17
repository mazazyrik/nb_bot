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
    redis_url: str = Field('redis://localhost:6379/0', env='REDIS_URL')
    admin_id: int = Field(0, env='ADMIN_ID')
    moderator_id: int = Field(0, env='MODERATOR_ID')
    moderator_ids: str = Field('', env='MODERATOR_IDS')

    postgres_user: str = Field(..., env='POSTGRES_USER')
    postgres_password: str = Field(..., env='POSTGRES_PASSWORD')
    postgres_host: str = Field(..., env='POSTGRES_HOST')
    postgres_port: int = Field(..., env='POSTGRES_PORT')
    postgres_db: str = Field(..., env='POSTGRES_DB')

    yandex_gpt_oauth_token: str = Field(..., env='YANDEX_GPT_OAUTH_TOKEN')
    yandex_gpt_folder_id: str = Field(..., env='YANDEX_GPT_FOLDER_ID')

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        env_file_encoding = 'utf-8'
        extra = 'ignore'

    def _get_parse_mode(self):
        if self.parse_mode not in ParseMode.__members__:
            raise EnvVarNotFoundException('PARSE_MODE')

    def get_moderator_ids(self) -> set[int]:
        ids: set[int] = set()
        if self.moderator_id:
            ids.add(int(self.moderator_id))

        raw = (self.moderator_ids or '').strip()
        if raw:
            parts = raw.replace(';', ',').split(',')
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                try:
                    ids.add(int(part))
                except ValueError:
                    continue
        return ids
