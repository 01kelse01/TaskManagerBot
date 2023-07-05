import asyncpg.exceptions
from aiogram import Dispatcher, Bot
from aiogram.types import Message

from tg_bot.models.postgresql import Database


async def user_start(message: Message, db: Database):
    try:
        user = await db.add_user(
            fullname=message.from_user.full_name,
            username=message.from_user.username,
            telegram_id=message.from_user.id
        )
        print(user)
    except asyncpg.exceptions.UniqueViolationError:
        print("?")
        user = await db.select_user(telegram_id=message.from_user.id)
        print(user)

    count = await db.select_count_users()
    await message.answer('\n'.join([
        f'Привіт, {message.from_user.full_name}',
        f'В базі всього '
        f'{count}'
    ]))
    print(user)


def register_user_in_users(dp: Dispatcher, db: Database):
    dp.register_message_handler(lambda message: user_start(message, db), commands="my_start")
