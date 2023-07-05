from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Створити задачу'),
            KeyboardButton(text='Інформація про задачу'),
        ],
        [
            KeyboardButton(text='Редагувати задачу'),
            KeyboardButton(text='Доступні задачі'),
        ],
        [
            KeyboardButton(text='Видалити задачу'),
            KeyboardButton(text='Інше...')
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    row_width=2
)
