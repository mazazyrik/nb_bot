import logging
from typing import Optional

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from crud.enums import RoleEnum
from crud.models import Admin, LookRequest, Visitor
from texts import (
    LOOK_REVIEW_CAPTION_TEXT,
    LOOK_REVIEW_COMMENT_BUTTON_TEXT,
    LOOK_REVIEW_OK_BUTTON_TEXT,
    NO_PERMISSIONS_TEXT,
)


logger = logging.getLogger(__name__)
moderator_router = Router()


def _refresh_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text='Обновить', callback_data='moderator_looks_refresh')]
        ]
    )


def _review_keyboard(request_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=LOOK_REVIEW_OK_BUTTON_TEXT,
                    callback_data=f'look_approve:{request_id}',
                ),
                InlineKeyboardButton(
                    text=LOOK_REVIEW_COMMENT_BUTTON_TEXT,
                    callback_data=f'look_comment:{request_id}',
                ),
            ]
        ]
    )


async def _caption_for_request(request: LookRequest) -> str:
    visitor = await Visitor.get_or_none(telegram_id=request.visitor_telegram_id)
    name = visitor.full_name if visitor is not None else ''
    username = visitor.telegram_username if visitor is not None else ''
    return LOOK_REVIEW_CAPTION_TEXT.format(
        visitor_telegram_id=request.visitor_telegram_id,
        visitor_name=name,
        visitor_username=username or '',
    )


async def _send_pending_requests(message: Message) -> None:
    pending = await LookRequest.filter(status='pending')
    if not pending:
        await message.answer(text='Активных заявок нет', reply_markup=_refresh_keyboard())
        return

    await message.answer(text=f'Активных заявок: {len(pending)}', reply_markup=_refresh_keyboard())
    for request in pending:
        caption = await _caption_for_request(request)
        try:
            await message.answer_photo(
                photo=request.photo_file_id,
                caption=caption,
                reply_markup=_review_keyboard(str(request.id)),
            )
        except Exception:
            logger.exception('failed to send pending look %s', request.id)


def _is_moderator(admin: Optional[Admin], role: Optional[RoleEnum]) -> bool:
    return admin is not None and role == RoleEnum.MODERATOR


@moderator_router.message(Command('_moderator'))
async def moderator_entry(
    message: Message, admin: Optional[Admin], admin_role: Optional[RoleEnum]
) -> None:
    if not _is_moderator(admin, admin_role):
        await message.answer(text=NO_PERMISSIONS_TEXT)
        return
    await _send_pending_requests(message)


@moderator_router.callback_query(F.data == 'moderator_looks_refresh')
async def moderator_refresh(
    callback: CallbackQuery, admin: Optional[Admin], admin_role: Optional[RoleEnum]
) -> None:
    if not _is_moderator(admin, admin_role):
        await callback.answer()
        return
    if callback.message is not None:
        await _send_pending_requests(callback.message)
    await callback.answer()
