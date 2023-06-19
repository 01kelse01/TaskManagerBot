from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Створити задачу')
        ],
        [
            KeyboardButton(text='Інформація про задачу')
        ],
        [
            KeyboardButton(text='Видалити задачу')
        ]
    ],
    resize_keyboard=True,
    row_width=4,
    is_persistent=True
)
