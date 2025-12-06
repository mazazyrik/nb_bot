from enum import Enum


class RoleEnum(str, Enum):
    ADMIN = 'Админ'
    MODERATOR = 'Модератор'
    HEAD = 'Глава рабочей группы'


class InstitutueEnum(str, Enum):
    IGSU = 'ИГСУ'
    INUP = 'ИнУп'
    ION = 'ИОН'
    IPNB = 'ИПНБ'
    IEMIT = 'ИЭМИТ'
    RR = 'РЕСУРС России'
