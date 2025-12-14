import asyncio
import logging
from typing import Optional

from aiogram import F, Router
from aiogram.filters import Command
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
from settings import Settings
from texts import LOOK_REVIEW_CAPTION_TEXT, LOOK_REVIEW_COMMENT_BUTTON_TEXT, LOOK_REVIEW_OK_BUTTON_TEXT, NO_PERMISSIONS_TEXT


logger = logging.getLogger(__name__)
admin_router = Router()


class AdminState(StatesGroup):
    waiting_assign_id = State()


def _admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='Назначить модератора',
                    callback_data='admin_assign:moderator',
                ),
                InlineKeyboardButton(
                    text='Назначить главу',
                    callback_data='admin_assign:head',
                ),
            ],
            [
                InlineKeyboardButton(
                    text='Все юзеры',
                    callback_data='admin_users',
                )
            ],
            [
                InlineKeyboardButton(
                    text='Висящие луки',
                    callback_data='admin_looks_pending',
                ),
                InlineKeyboardButton(
                    text='Одобренные луки',
                    callback_data='admin_looks_approved',
                ),
            ],
        ]
    )


def _cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='Отмена',
                    callback_data='admin_cancel',
                )
            ]
        ]
    )


def _is_owner(user_id: int) -> bool:
    settings = Settings()
    return bool(settings.admin_id) and user_id == settings.admin_id


def _role_from_key(key: str) -> Optional[RoleEnum]:
    if key == 'moderator':
        return RoleEnum.MODERATOR
    if key == 'head':
        return RoleEnum.HEAD
    return None


async def _ensure_owner_admin(message: Message) -> None:
    settings = Settings()
    if not settings.admin_id:
        return
    admin, created = await Admin.get_or_create(
        telegram_id=settings.admin_id,
        defaults={
            'username': message.from_user.username,
            'role': RoleEnum.ADMIN,
        },
    )
    if not created and admin.role != RoleEnum.ADMIN:
        admin.role = RoleEnum.ADMIN
        await admin.save()
    if not admin.username and message.from_user.username:
        admin.username = message.from_user.username
        await admin.save()


@admin_router.message(Command('_admin'))
async def admin_entry(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id):
        await message.answer(text=NO_PERMISSIONS_TEXT)
        return
    await _ensure_owner_admin(message)
    await state.clear()
    await message.answer(text='Админка', reply_markup=_admin_keyboard())


@admin_router.callback_query(F.data.startswith('admin_assign:'))
async def admin_assign_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_owner(callback.from_user.id):
        await callback.answer()
        return
    parts = (callback.data or '').split(':', 1)
    if len(parts) != 2:
        await callback.answer()
        return

    role = _role_from_key(parts[1])
    if role is None:
        await callback.answer()
        return

    await state.set_state(AdminState.waiting_assign_id)
    await state.update_data(assign_role=role.value)
    if callback.message is not None:
        await callback.message.answer(
            text='Скинь Telegram ID пользователя',
            reply_markup=_cancel_keyboard(),
        )
    await callback.answer()


@admin_router.callback_query(F.data == 'admin_cancel')
async def admin_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_owner(callback.from_user.id):
        await callback.answer()
        return
    await state.clear()
    await callback.answer()


@admin_router.message(AdminState.waiting_assign_id)
async def admin_assign_finish(message: Message, state: FSMContext) -> None:
    if not _is_owner(message.from_user.id):
        await state.clear()
        return

    raw = (message.text or '').strip()
    if not raw.isdigit():
        await message.answer(text='Нужен числовой Telegram ID', reply_markup=_cancel_keyboard())
        return

    data = await state.get_data()
    role_value = str(data.get('assign_role') or '')
    try:
        role = RoleEnum(role_value)
    except ValueError:
        await state.clear()
        return

    telegram_id = int(raw)
    admin, created = await Admin.get_or_create(
        telegram_id=telegram_id,
        defaults={
            'username': None,
            'role': role,
        },
    )
    if not created and admin.role != role:
        admin.role = role
        await admin.save()

    await state.clear()
    await message.answer(text=f'Готово: {telegram_id} -> {role.value}')


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


@admin_router.callback_query(F.data == 'admin_users')
async def admin_users(callback: CallbackQuery) -> None:
    if not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    usernames = await Visitor.exclude(telegram_username__isnull=True).values_list(
        'telegram_username',
        flat=True,
    )
    lines = [f'@{u}' for u in sorted({u for u in usernames if u})]
    if not lines:
        if callback.message is not None:
            await callback.message.answer(text='Пока пусто')
        await callback.answer()
        return

    for chunk in _chunk_lines(lines):
        if callback.message is not None:
            await callback.message.answer(text=chunk)
    await callback.answer()


@admin_router.callback_query(F.data == 'admin_looks_pending')
async def admin_looks_pending(callback: CallbackQuery) -> None:
    if not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    pending = await LookRequest.filter(status='pending')
    if not pending:
        if callback.message is not None:
            await callback.message.answer(text='Активных заявок нет')
        await callback.answer()
        return

    if callback.message is not None:
        await callback.message.answer(text=f'Активных заявок: {len(pending)}')
        for idx, request in enumerate(pending):
            caption = await _caption_for_request(request)
            try:
                await callback.message.answer_photo(
                    photo=request.photo_file_id,
                    caption=caption,
                    reply_markup=_review_keyboard(str(request.id)),
                )
            except Exception:
                logger.exception('failed to send pending look %s', request.id)
            if (idx + 1) % 3 == 0 and (idx + 1) < len(pending):
                await asyncio.sleep(1)

    await callback.answer()


@admin_router.callback_query(F.data == 'admin_looks_approved')
async def admin_looks_approved(callback: CallbackQuery) -> None:
    if not _is_owner(callback.from_user.id):
        await callback.answer()
        return

    approved = await LookRequest.filter(status='approved')
    if not approved:
        if callback.message is not None:
            await callback.message.answer(text='Одобренных заявок нет')
        await callback.answer()
        return

    if callback.message is not None:
        await callback.message.answer(text=f'Одобренных заявок: {len(approved)}')
        for idx, request in enumerate(approved):
            caption = await _caption_for_request(request)
            try:
                await callback.message.answer_photo(
                    photo=request.photo_file_id,
                    caption=caption,
                )
            except Exception:
                logger.exception('failed to send approved look %s', request.id)
            if (idx + 1) % 3 == 0 and (idx + 1) < len(approved):
                await asyncio.sleep(1)

    await callback.answer()


