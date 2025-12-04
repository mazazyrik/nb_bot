from typing import Any, Awaitable, Callable, Dict, Iterable, Optional

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update

from crud.enums import RoleEnum
from crud.exceptions import AdminNotFound
from crud.models import Admin


EventType = Message | CallbackQuery | Update
HandlerType = Callable[[EventType, Dict[str, Any]], Awaitable[Any]]


class AdminRoleMiddleware(BaseMiddleware):
    def __init__(self, allowed_roles: Optional[Iterable[RoleEnum]] = None) -> None:
        self.allowed_roles = set(allowed_roles) if allowed_roles is not None else None

    async def __call__(
        self,
        handler: HandlerType,
        event: EventType,
        data: Dict[str, Any],
    ) -> Any:
        from_user = getattr(event, 'from_user', None)
        if from_user is None:
            return await handler(event, data)

        telegram_id = from_user.id
        admin = await Admin.get_or_none(telegram_id=telegram_id)
        if admin is None:
            raise AdminNotFound(telegram_id)

        data['admin'] = admin
        data['admin_role'] = admin.role

        if self.allowed_roles is not None and admin.role not in self.allowed_roles:
            bot = data.get('bot')
            if bot is not None and hasattr(event, 'chat'):
                await bot.send_message(
                    chat_id=event.chat.id, text='у вас нет прав для этой команды'
                )
            return None

        return await handler(event, data)
