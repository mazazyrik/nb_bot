from typing import Optional

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from crud.models import Visitor
from gpt import get_completion
from texts import (
    WELCOME_IMAGE_URL,
    WISH_ALREADY_EXISTS_INFO_TEXT,
    WISH_LOADING_TEXT,
    WISH_NOT_REGISTERED_TEXT,
)


whishes_router = Router()


@whishes_router.message(Command('wish'))
async def send_whish(message: Message, visitor: Optional[Visitor]) -> None:
    if visitor is None:
        await message.answer(text=WISH_NOT_REGISTERED_TEXT)
        return

    if visitor.whish:
        await message.answer(text=WISH_ALREADY_EXISTS_INFO_TEXT)
        await message.answer(text=visitor.whish)
        return

    name = message.from_user.first_name or 'гость'
    loading_message = await message.answer_photo(
        photo=WELCOME_IMAGE_URL,
        caption=WISH_LOADING_TEXT,
    )

    whish_text = await get_completion(name)
    if not whish_text:
        await loading_message.edit_caption(
            caption='Что-то пошло не так, попробуй ещё раз чуть позже.'
        )
        return

    visitor.whish = whish_text
    await visitor.save()

    await loading_message.edit_caption(caption=whish_text)
