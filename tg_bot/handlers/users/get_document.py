from aiogram import Bot, Dispatcher, types
from aiogram.types import Message


def handler_document_wrapper(bot: Bot):
    async def handler_document(message: Message):
        # Отримуємо файл та здерігаємо у БД
        file_id = message.document.file_id
        file_name = message.document.file_name
        file_url = bot.get_file_url(file_id)
        print(file_id)
        print(file_name)
        print(file_url)
        await message.answer(f"Отримав)")
        await message.reply("Але ще не знаю, що з ним зробити 😭")

    return handler_document


def register_files(dp: Dispatcher, bot: Bot):
    dp.register_message_handler(handler_document_wrapper(bot), content_types=types.ContentType.DOCUMENT)
