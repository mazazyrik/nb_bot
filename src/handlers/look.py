from __future__ import annotations

import logging
from typing import Iterable, Optional
from uuid import UUID

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from crud.enums import RoleEnum
from crud.models import Admin, LookRequest, Visitor
from texts import (
    LOOK_APPROVED_TEXT,
    LOOK_CANCEL_BUTTON_TEXT,
    LOOK_CANCELLED_TEXT,
    LOOK_COMMENT_CANCEL_BUTTON_TEXT,
    LOOK_COMMENT_PROMPT_TEXT,
    LOOK_NEED_PHOTO_TEXT,
    LOOK_REVIEW_CAPTION_TEXT,
    LOOK_REVIEW_COMMENT_BUTTON_TEXT,
    LOOK_REVIEW_OK_BUTTON_TEXT,
    LOOK_SENT_FOR_REVIEW_TEXT,
    LOOK_WAITING_PHOTO_TEXT,
)


logger = logging.getLogger(__name__)
look_router = Router()


class LookState(StatesGroup):
    waiting_photo = State()


class LookModerationState(StatesGroup):
    waiting_comment = State()


def _cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=LOOK_CANCEL_BUTTON_TEXT,
                    callback_data='look_cancel',
                )
            ]
        ]
    )


def _comment_cancel_keyboard(request_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=LOOK_COMMENT_CANCEL_BUTTON_TEXT,
                    callback_data=f'look_comment_cancel:{request_id}',
                )
            ]
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


async def _iter_reviewer_ids() -> list[int]:
    moderators = await Admin.filter(role=RoleEnum.MODERATOR).values_list('telegram_id', flat=True)
    ids = {int(x) for x in list(moderators) if x is not None}
    return sorted(ids)


async def _safe_send_photo_to_reviewers(
    *,
    message: Message,
    reviewer_ids: Iterable[int],
    photo_file_id: str,
    caption: str,
    reply_markup: InlineKeyboardMarkup,
) -> None:
    for chat_id in reviewer_ids:
        try:
            await message.bot.send_photo(
                chat_id=chat_id,
                photo=photo_file_id,
                caption=caption,
                reply_markup=reply_markup,
            )
        except Exception:
            logger.exception('failed to send look photo to reviewer %s', chat_id)


@look_router.callback_query(F.data == 'menu_rate_look')
async def look_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(LookState.waiting_photo)
    if callback.message is not None:
        await callback.message.answer(
            text=LOOK_WAITING_PHOTO_TEXT,
            reply_markup=_cancel_keyboard(),
        )
    await callback.answer()


@look_router.callback_query(F.data == 'look_cancel')
async def look_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    if callback.message is not None:
        await callback.message.answer(text=LOOK_CANCELLED_TEXT)
    await callback.answer()


@look_router.message(LookState.waiting_photo)
async def look_receive_photo(
    message: Message,
    state: FSMContext,
    visitor: Optional[Visitor],
) -> None:
    if not message.photo:
        await message.answer(
            text=LOOK_NEED_PHOTO_TEXT,
            reply_markup=_cancel_keyboard(),
        )
        return

    photo_file_id = message.photo[-1].file_id
    request = await LookRequest.create(
        visitor_telegram_id=message.from_user.id,
        photo_file_id=photo_file_id,
    )

    reviewer_ids = await _iter_reviewer_ids()
    name = visitor.full_name if visitor is not None else ''
    username = message.from_user.username or ''
    caption = LOOK_REVIEW_CAPTION_TEXT.format(
        visitor_telegram_id=message.from_user.id,
        visitor_name=name,
        visitor_username=username,
    )

    await _safe_send_photo_to_reviewers(
        message=message,
        reviewer_ids=reviewer_ids,
        photo_file_id=photo_file_id,
        caption=caption,
        reply_markup=_review_keyboard(str(request.id)),
    )

    await state.clear()
    await message.answer(text=LOOK_SENT_FOR_REVIEW_TEXT)


@look_router.callback_query(F.data.startswith('look_approve:'))
async def look_approve(
    callback: CallbackQuery,
    admin: Optional[Admin],
    admin_role: Optional[RoleEnum],
) -> None:
    if admin_role not in {RoleEnum.ADMIN, RoleEnum.MODERATOR}:
        await callback.answer()
        return

    parts = (callback.data or '').split(':', 1)
    if len(parts) != 2:
        await callback.answer()
        return

    request_id_raw = parts[1]
    try:
        request_id = UUID(request_id_raw)
    except ValueError:
        await callback.answer()
        return

    request = await LookRequest.get_or_none(id=request_id)
    if request is None:
        await callback.answer()
        return

    if request.status != 'approved':
        request.status = 'approved'
        await request.save()
        try:
            await callback.bot.send_message(
                chat_id=request.visitor_telegram_id,
                text=LOOK_APPROVED_TEXT,
            )
        except Exception:
            logger.exception('failed to notify visitor about approval %s', request.visitor_telegram_id)

    if callback.message is not None:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass

    await callback.answer()


@look_router.callback_query(F.data.startswith('look_comment:'))
async def look_comment_start(
    callback: CallbackQuery,
    state: FSMContext,
    admin: Optional[Admin],
    admin_role: Optional[RoleEnum],
) -> None:
    if admin_role not in {RoleEnum.ADMIN, RoleEnum.MODERATOR}:
        await callback.answer()
        return

    parts = (callback.data or '').split(':', 1)
    if len(parts) != 2:
        await callback.answer()
        return

    request_id = parts[1]
    await state.set_state(LookModerationState.waiting_comment)
    await state.update_data(look_request_id=request_id)
    if callback.message is not None:
        await callback.message.answer(
            text=LOOK_COMMENT_PROMPT_TEXT,
            reply_markup=_comment_cancel_keyboard(request_id),
        )
    await callback.answer()


@look_router.callback_query(F.data.startswith('look_comment_cancel:'))
async def look_comment_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()


@look_router.message(LookModerationState.waiting_comment)
async def look_comment_send(
    message: Message,
    state: FSMContext,
    admin_role: Optional[RoleEnum],
) -> None:
    if admin_role not in {RoleEnum.ADMIN, RoleEnum.MODERATOR}:
        await state.clear()
        return

    text = (message.text or '').strip()
    if not text:
        data = await state.get_data()
        request_id = str(data.get('look_request_id') or '')
        await message.answer(
            text=LOOK_COMMENT_PROMPT_TEXT,
            reply_markup=_comment_cancel_keyboard(request_id),
        )
        return

    data = await state.get_data()
    request_id_raw = str(data.get('look_request_id') or '')
    try:
        request_id = UUID(request_id_raw)
    except ValueError:
        await state.clear()
        return

    request = await LookRequest.get_or_none(id=request_id)
    if request is None:
        await state.clear()
        return

    try:
        await message.bot.send_message(
            chat_id=request.visitor_telegram_id,
            text=f'Ответственный за костюмы написал:\n{text}',
        )
    except Exception:
        logger.exception('failed to send look comment to visitor %s', request.visitor_telegram_id)
        await message.answer(text='Не получилось отправить сообщение, попробуй ещё раз')
        return

    request.status = 'commented'
    await request.save()

    await state.clear()
    await message.answer(text='Сообщение отправлено')


