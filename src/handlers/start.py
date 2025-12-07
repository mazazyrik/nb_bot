from typing import Optional

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from crud.enums import RoleEnum
from crud.models import Admin, Visitor
from handlers.registration import get_menu_keyboard, start_registration
from texts import (
    START_ADMIN_TEXT,
    START_HEAD_TEXT,
    START_MODERATOR_TEXT,
    START_VISITOR_RETURN_TEXT,
    WELCOME_IMAGE_URL,
)


start_router = Router()


@start_router.message(CommandStart())
async def start(
    message: Message,
    admin: Optional[Admin],
    admin_role: Optional[RoleEnum],
    visitor: Optional[Visitor],
    state: FSMContext,
) -> None:
    await message.answer_photo(photo=WELCOME_IMAGE_URL)

    if admin:
        if admin_role == RoleEnum.ADMIN:
            await message.answer(
                text=START_ADMIN_TEXT,
            )
        elif admin_role == RoleEnum.MODERATOR:
            await message.answer(
                text=START_MODERATOR_TEXT,
            )
        elif admin_role == RoleEnum.HEAD:
            await message.answer(
                text=START_HEAD_TEXT,
            )
        return

    if visitor:
        await message.answer(
            text=START_VISITOR_RETURN_TEXT,
            reply_markup=get_menu_keyboard(),
        )
        return

    await start_registration(message, state)
