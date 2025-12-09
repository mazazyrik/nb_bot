from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from texts import (
    MENU_DESCRIPTION_TEXT,
    MENU_IMAGE_URL,
    MENU_RATE_LOOK_STUB_TEXT,
)


menu_router = Router()


def get_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Частые вопросы', callback_data='menu_faq'),
            ],
            [
                InlineKeyboardButton(
                    text='Оценить лук',
                    callback_data='menu_rate_look',
                ),
            ],
            [
                InlineKeyboardButton(
                    text='Получить предсказание', callback_data='menu_prediction'
                ),
            ],
        ]
    )


async def send_menu(message: Message) -> None:
    await message.answer_photo(
        photo=MENU_IMAGE_URL,
        caption=MENU_DESCRIPTION_TEXT,
        reply_markup=get_menu_keyboard(),
    )


@menu_router.message(Command('menu'))
async def menu_command(message: Message) -> None:
    await send_menu(message)


@menu_router.callback_query(F.data == 'menu')
async def menu_entry_callback(callback: CallbackQuery) -> None:
    if callback.message is not None:
        await send_menu(callback.message)
    await callback.answer()


@menu_router.callback_query(F.data == 'menu_rate_look')
async def menu_rate_look(callback: CallbackQuery) -> None:
    if callback.message is not None:
        await callback.message.answer(text=MENU_RATE_LOOK_STUB_TEXT)
    await callback.answer()
