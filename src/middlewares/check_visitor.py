from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, Update

from crud.models import Visitor


EventType = Message | CallbackQuery | Update
HandlerType = Callable[[EventType, Dict[str, Any]], Awaitable[Any]]


class Auth(BaseMiddleware):
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
        visitor = await Visitor.get_or_none(telegram_id=telegram_id)
        data['visitor'] = visitor

        return await handler(event, data)
