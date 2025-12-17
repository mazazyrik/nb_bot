import asyncio
import logging
from typing import Optional

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from crud.enums import RoleEnum
from crud.models import Admin, LookRequest, Visitor
from crud.operations import get_look_requests_counts, get_users_count
from texts import LOOK_REVIEW_CAPTION_TEXT, NO_PERMISSIONS_TEXT


logger = logging.getLogger(__name__)
head_router = Router()


def _is_head(admin: Optional[Admin], role: Optional[RoleEnum]) -> bool:
    return role == RoleEnum.HEAD


def _head_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Все юзеры', callback_data='head_users'),
                InlineKeyboardButton(text='Одобренные луки', callback_data='head_looks'),
            ],
            [
                InlineKeyboardButton(text='Кол-во пользователей', callback_data='head_stats_users'),
                InlineKeyboardButton(text='Кол-во заявок', callback_data='head_stats_requests'),
            ],
        ]
    )


def _users_refresh_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='Обновить', callback_data='head_users')]]
    )


def _looks_refresh_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='Обновить', callback_data='head_looks')]]
    )


def _chunk_lines(lines: list[str], limit: int = 3500) -> list[str]:
    chunks: list[str] = []
    buf = ''
    for line in lines:
        candidate = f'{buf}\n{line}' if buf else line
        if len(candidate) > limit:
            if buf:
                chunks.append(buf)
            buf = line
        else:
            buf = candidate
    if buf:
        chunks.append(buf)
    return chunks


async def _send_users(message: Message) -> None:
    usernames = await Visitor.exclude(telegram_username__isnull=True).values_list(
        'telegram_username',
        flat=True,
    )
    lines = [f'@{u}' for u in sorted({u for u in usernames if u})]
    if not lines:
        await message.answer(text='Пока пусто', reply_markup=_users_refresh_keyboard())
        return

    await message.answer(text=f'Пользователей: {len(lines)}', reply_markup=_users_refresh_keyboard())
    for chunk in _chunk_lines(lines):
        await message.answer(text=chunk)


async def _caption_for_request(request: LookRequest) -> str:
    visitor = await Visitor.get_or_none(telegram_id=request.visitor_telegram_id)
    name = visitor.full_name if visitor is not None else ''
    username = visitor.telegram_username if visitor is not None else ''
    return LOOK_REVIEW_CAPTION_TEXT.format(
        visitor_telegram_id=request.visitor_telegram_id,
        visitor_name=name,
        visitor_username=username or '',
    )


async def _send_approved_looks(message: Message) -> None:
    approved = await LookRequest.filter(status='approved')
    if not approved:
        await message.answer(text='Одобренных заявок нет', reply_markup=_looks_refresh_keyboard())
        return

    await message.answer(
        text=f'Одобренных заявок: {len(approved)}',
        reply_markup=_looks_refresh_keyboard(),
    )
    for idx, request in enumerate(approved):
        caption = await _caption_for_request(request)
        try:
            await message.answer_photo(
                photo=request.photo_file_id,
                caption=caption,
            )
        except Exception:
            logger.exception('failed to send approved look %s', request.id)
        if (idx + 1) % 3 == 0 and (idx + 1) < len(approved):
            await asyncio.sleep(1)


@head_router.message(Command('_head'))
async def head_entry(message: Message, admin: Optional[Admin], admin_role: Optional[RoleEnum]) -> None:
    if not _is_head(admin, admin_role):
        await message.answer(text=NO_PERMISSIONS_TEXT)
        return
    await message.answer(text='Панель главы', reply_markup=_head_keyboard())


@head_router.callback_query(F.data == 'head_users')
async def head_users(
    callback: CallbackQuery, admin: Optional[Admin], admin_role: Optional[RoleEnum]
) -> None:
    if not _is_head(admin, admin_role):
        await callback.answer()
        return
    if callback.message is not None:
        await _send_users(callback.message)
    await callback.answer()


@head_router.callback_query(F.data == 'head_looks')
async def head_looks(
    callback: CallbackQuery, admin: Optional[Admin], admin_role: Optional[RoleEnum]
) -> None:
    if not _is_head(admin, admin_role):
        await callback.answer()
        return
    if callback.message is not None:
        await _send_approved_looks(callback.message)
    await callback.answer()


@head_router.callback_query(F.data == 'head_stats_users')
async def head_stats_users(
    callback: CallbackQuery,
    admin: Optional[Admin],
    admin_role: Optional[RoleEnum],
) -> None:
    if not _is_head(admin, admin_role):
        await callback.answer()
        return
    count = await get_users_count()
    if callback.message is not None:
        await callback.message.answer(text=f'Пользователей: {count}')
    await callback.answer()


@head_router.callback_query(F.data == 'head_stats_requests')
async def head_stats_requests(
    callback: CallbackQuery,
    admin: Optional[Admin],
    admin_role: Optional[RoleEnum],
) -> None:
    if not _is_head(admin, admin_role):
        await callback.answer()
        return
    counts = await get_look_requests_counts()
    total = counts.get('total', 0)
    processed = counts.get('processed', 0)
    pending = counts.get('pending', 0)
    approved = counts.get('approved', 0)
    commented = counts.get('commented', 0)
    text = (
        'Заявки:\n'
        f'всего: {total}\n'
        f'обработано: {processed}\n'
        f'висящих: {pending}\n'
        f'одобрено: {approved}\n'
        f'с комментом: {commented}'
    )
    if callback.message is not None:
        await callback.message.answer(text=text)
    await callback.answer()


