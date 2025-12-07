import json
from pathlib import Path

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from texts import FAQ_LIST_TITLE_TEXT


faq_router = Router()


FAQ_PATH = Path(__file__).resolve().parent.parent.parent / 'faq.json'

with FAQ_PATH.open('r', encoding='utf-8') as f:
    _FAQ_DATA = json.load(f)


def get_faq_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for index, item in enumerate(_FAQ_DATA):
        rows.append(
            [
                InlineKeyboardButton(
                    text=item.get('question', ''),
                    callback_data=f'faq_q_{index}',
                ),
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text='⬅️ В меню',
                callback_data='menu',
            ),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


@faq_router.callback_query(F.data == 'menu_faq')
async def open_faq(callback: CallbackQuery) -> None:
    message = callback.message
    if message is None:
        await callback.answer()
        return

    # если сообщение с фото и подписью (как меню) — редактируем подпись
    if message.photo:
        await message.edit_caption(
            caption=FAQ_LIST_TITLE_TEXT,
            reply_markup=get_faq_keyboard(),
        )
    else:
        await message.edit_text(
            text=FAQ_LIST_TITLE_TEXT,
            reply_markup=get_faq_keyboard(),
        )

    await callback.answer()


@faq_router.callback_query(F.data.startswith('faq_q_'))
async def show_faq_answer(callback: CallbackQuery) -> None:
    message = callback.message
    if message is None or callback.data is None:
        await callback.answer()
        return

    try:
        index = int(callback.data.split('_')[-1])
    except ValueError:
        await callback.answer()
        return

    if index < 0 or index >= len(_FAQ_DATA):
        await callback.answer()
        return

    item = _FAQ_DATA[index]
    question = item.get('question', '')
    answer = item.get('answer', '')

    text = (
        f'❓ {question}\n\n'
        f'{answer}\n\n'
        'Вы можете выбрать другой вопрос или вернуться в меню.'
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='⬅️ К вопросам',
                    callback_data='menu_faq',
                ),
            ],
            [
                InlineKeyboardButton(
                    text='⬅️ В меню',
                    callback_data='menu',
                ),
            ],
        ]
    )

    if message.photo:
        await message.edit_caption(
            caption=text,
            reply_markup=keyboard,
        )
    else:
        await message.edit_text(
            text=text,
            reply_markup=keyboard,
        )

    await callback.answer()
