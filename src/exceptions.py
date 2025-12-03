import logging


logger = logging.getLogger(__name__)


class EnvVarNotFoundException(Exception):
    def __init__(self, value) -> None:
        self._value = value
        logger.error('env var not found: %s', value)
        super().__init__(
            f'При инициализации проекта не найдена переменная окружения: {self._value}'
        )