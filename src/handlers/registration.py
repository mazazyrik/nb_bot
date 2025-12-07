from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from crud.enums import InstitutueEnum
from crud.models import Visitor
from members_json import check
from texts import (
    BUTTON_MENU_TEXT,
    REGISTRATION_ASK_FULL_NAME,
    REGISTRATION_ASK_PHONE,
    REGISTRATION_FULL_NAME_RETRY,
    REGISTRATION_NOT_FOUND_RETRY,
    REGISTRATION_SUCCESS,
)


registration_router = Router()


class RegistrationState(StatesGroup):
    waiting_full_name = State()
    waiting_phone = State()


def get_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BUTTON_MENU_TEXT, callback_data='menu')],
        ],
    )


async def start_registration(message: Message, state: FSMContext) -> None:
    await state.set_state(RegistrationState.waiting_full_name)
    await message.answer(
        text=REGISTRATION_ASK_FULL_NAME,
    )


@registration_router.message(RegistrationState.waiting_full_name)
async def process_full_name(message: Message, state: FSMContext) -> None:
    full_name = (message.text or '').strip()
    if len(full_name.split()) < 3:
        await message.answer(
            text=REGISTRATION_FULL_NAME_RETRY,
        )
        return

    await state.update_data(full_name=full_name)
    await state.set_state(RegistrationState.waiting_phone)
    await message.answer(
        text=REGISTRATION_ASK_PHONE,
    )


@registration_router.message(RegistrationState.waiting_phone)
async def process_phone(message: Message, state: FSMContext) -> None:
    phone = (message.text or '').strip()
    data = await state.get_data()
    full_name = data.get('full_name')
    matches = await check(full_name=full_name, phone=phone)

    if not matches:
        await message.answer(
            text=REGISTRATION_NOT_FOUND_RETRY,
        )
        await start_registration(message, state)
        return

    record = matches[0]
    program_value = record.get('Институт/программа')
    grade = record.get('Курс') or ''
    phone_value = record.get('Номер телефона') or phone
    email = record.get('Электронная почта') or ''
    program = (
        InstitutueEnum(program_value) if program_value is not None else None
    )

    await Visitor.get_or_create(
        telegram_id=message.from_user.id,
        defaults={
            'full_name': record.get('ФИО', full_name),
            'program': program,
            'grade': grade,
            'phone': phone_value,
            'email': email,
        },
    )

    await state.clear()
    await message.answer(
        text=REGISTRATION_SUCCESS,
        reply_markup=get_menu_keyboard(),
    )
