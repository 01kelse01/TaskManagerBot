from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault


async def set_default_commands(bot: Bot):
    await bot.set_my_commands(
        commands=[
            BotCommand("start", 'Почати заново'),
        ],
        scope=BotCommandScopeDefault(),

    )
