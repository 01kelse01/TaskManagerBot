from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hcode


async def bot_echo(message: types.Message):
    text = [
        "Ехо без стану.",
        "Повідомлення:",
        message.text
    ]

    await message.answer('\n'.join(text))


async def bot_echo_all(message: types.Message, state: FSMContext):
    state_name = await state.get_state()
    text = [
        f'Ехо в стані {hcode(state_name)}',
        'Зміст повідомлення:',
        hcode(message.text)
    ]
    await message.answer('\n'.join(text))


async def my_bot_echo(message: types.Message):
    await message.answer("Якщо потрібна моя допомога, натисніть на клавіатурі відповідні кнопки!")


def register_echo(dp: Dispatcher):
    # dp.register_message_handler(bot_echo)
    # dp.register_message_handler(bot_echo_all, state="*", content_types=types.ContentTypes.ANY)
    dp.register_message_handler(my_bot_echo)
