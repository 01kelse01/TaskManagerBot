from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from tg_bot.keyboards.inline.callback_datas import choice_callback

choice = InlineKeyboardMarkup(row_width=1, inline_keyboard=[
    [
        InlineKeyboardButton(
            text="Відправити",
            callback_data=choice_callback.new(name='send')
        )
    ]

])
take_task = InlineKeyboardMarkup(row_width=1, inline_keyboard=[
    [
        InlineKeyboardButton(
            text="Взяти в роботу",
            callback_data=choice_callback.new(name="take_task")
        )
    ],

])

done = InlineKeyboardMarkup(row_width=1, inline_keyboard=[
    [
        InlineKeyboardButton(
            text='Позначити як виконану',
            callback_data=choice_callback.new(name='done')
        )
    ]
])

take = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(
            text="Взяти до роботи",
            callback_data=choice_callback.new(name='take_new_task')
        )
    ]
])
