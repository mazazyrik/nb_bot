from typing import Optional

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from crud.models import Visitor
from crud.operations import get_visitor_name
from gpt import get_completion
from texts import (
    BUTTON_MENU_TEXT,
    WELCOME_IMAGE_URL,
    WISH_ALREADY_EXISTS_INFO_TEXT,
    WISH_LOADING_TEXT,
    WISH_NOT_REGISTERED_TEXT,
)


whishes_router = Router()


async def _process_whish(message: Message, visitor: Optional[Visitor]) -> None:
    if visitor is None:
        await message.answer(text=WISH_NOT_REGISTERED_TEXT)
        return

    if visitor.whish:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=BUTTON_MENU_TEXT,
                        callback_data='menu',
                    ),
                ],
            ]
        )
        text = f'{WISH_ALREADY_EXISTS_INFO_TEXT}\n\n{visitor.whish}'
        await message.answer(
            text=text,
            reply_markup=keyboard,
        )
        return

    name = await get_visitor_name(message.from_user.id)
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


@whishes_router.callback_query(F.data == 'menu_prediction')
async def send_whish_callback(
    callback: CallbackQuery,
    visitor: Optional[Visitor],
) -> None:
    if callback.message is not None:
        await _process_whish(callback.message, visitor)
    await callback.answer()
