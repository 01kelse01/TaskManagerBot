from aiogram import Dispatcher, types, Bot
from aiogram.dispatcher import FSMContext

from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from tg_bot.keyboards.inline.callback_datas import choice_callback
from tg_bot.keyboards.inline.choice_buttons import choice, take_task, done
from tg_bot.keyboards.reply import menu
from tg_bot.models import sqlite
from tg_bot.misc.states import Task


# Starting
async def user_start(message: Message):
    await message.answer(f"Привіт, {message.from_user.full_name}")
    await message.answer("Я бот для створення задач.\nОберіть дії зі мною:", reply_markup=menu)


# Просто повертає id групи яка там вказана(якщо створити нову групу потрібно вказати її id)
def get_my_group_id():
    return -1001922917876


# Натискання на створення задачі
async def enter_create_task(message: Message):
    await message.answer("Введіть назву задачі:")

    # Очікуємо відповідь з назвою задачі
    await Task.waiting_for_task_name.set()


# Отримання назви задачі
async def answer_task_name(message: Message, state: FSMContext):
    # Отримуємо назву задачі та ID замовника з повідомлення
    task_name = message.text

    # Зберігаємо дані задачі в стані
    await state.update_data(task_name=task_name)

    # Очікуємо деталі завдання
    await message.answer("Введіть деталі завдання:")
    await Task.waiting_for_task_detail.set()


# Отримання деталей задачі
async def answer_task_detail(message: Message, state: FSMContext):
    # Отримуємо дані про задачу та замовника
    data = await state.get_data()
    user_name = message.from_user.full_name
    task_name = data.get('task_name')
    task_detail = message.text

    # _____________________________________________
    db = sqlite.Database()  # Операції з БД
    db.create_table_task()
    db.add_task((task_name, task_detail, 'В очікуванні', None, user_name))
    # Отримуємо id запису
    task_id = db.get_last_id()
    await state.update_data(id_task=task_id)
    # _____________________________________________

    await message.answer('\n'.join([
        'Задачу створено😊',
        f'ID задачі: {task_id}',
        f'Замовник: {user_name}',
        f'Назва: {task_name}',
        f'Деталі: {task_detail}',
    ]), reply_markup=choice)

    # Очікуємо відправки
    await Task.waiting_for_send_task.set()


# Надсилання задачі в групу
def enter_send_task_to_wrapper(bot: Bot):
    async def enter_send_task_to(call: CallbackQuery, state: FSMContext):
        # Отримання інформації зі стану
        data = await state.get_data()
        db = sqlite.Database()
        info = db.get_info_task(data.get('id_task'))

        # Відправляємо задачу разом з клавіатурою у груповий чат
        GROUP_CHAT_ID = get_my_group_id()
        task_text = '\n'.join([
            '✋',
            f'Нова задача від: {info[5]}',
            f'ID задачі: {info[0]}',
            f'Назва: {info[1]}',
            f'Опис: {info[2]}',
            f'Статус: {info[3]}'
        ])
        await bot.send_message(GROUP_CHAT_ID, task_text, reply_markup=take_task)
        # -------------------------------------------------------
        await call.message.reply("Задача надіслана!")
        await state.finish()

    return enter_send_task_to


# Отримання ID задачі
def get_id_task(callback: CallbackQuery) -> int:
    data_text = callback.message.text.split('\n')
    data = None
    for data in data_text:
        if data.startswith("ID"):
            data = data
            break
    id_task = int(str(data).split(":")[1].strip())
    return id_task


# Оновлення інформації про задачу
async def enter_take_task_in_group(call: CallbackQuery):
    performer = call.from_user.full_name

    # Отримання ID задачі
    data = tuple(call.message.text.split('\n'))[2]
    id_task = int(str(data).split(":")[1].strip())

    # Оновлення виконавця та її статусу
    db = sqlite.Database()
    db.update_task_performer(id_task, performer)
    db.update_task_status(id_task, 'В роботі')

    # Формування оновлення повідомлення
    info = db.get_info_task(id_task)
    task_text = '\n'.join([
        'Оновлено 📦',
        f'ID задачі: {info[0]}',
        f'Назва: {info[1]}',
        f'Опис: {info[2]}',
        f'Статус: {info[3]}',
        f'Виконавець: {info[5]}'
    ])
    await call.message.edit_text(task_text)
    await call.message.edit_reply_markup(reply_markup=done)
    await call.answer("Задачу взято в роботу!")


# Оновлення інформації про виконання
async def update_task_to_done(call: CallbackQuery):
    # Отримання ID задачі
    id_task = get_id_task(callback=call)
    # Оновлення статусу
    db = sqlite.Database()
    db.update_task_status(id_task, 'Виконано')

    # Формування оновлення повідомлення
    info = db.get_info_task(id_task)
    task_text = '\n'.join([
        'Оновлено 📦',
        f'ID задачі: {info[0]}',
        f'Назва: {info[1]}',
        f'Опис: {info[2]}',
        f'Статус: {info[3]}',
        f'Виконавець: {info[5]}'
    ])
    await call.message.edit_text(task_text)
    await call.answer("Задачу виконано!")


# End --------------------------------------------------------------------------------------------------------

# Інформація про задачу ---------start---------------
async def enter_info_task(message: Message):
    await message.answer("Введіть номер задачі яку Ви хочете переглянути:")

    # Очікування id задачі
    await Task.waiting_for_id_task_detail.set()


async def answer_info_task(message: Message, state: FSMContext):
    id_task = message.text
    await message.answer(f'Ви ввели -> {id_task}')

    # Операції з БД
    db = sqlite.Database()
    result = db.get_info_task(id_task)
    await message.answer('\n'.join([
        f'Дані про задачу:',
        f'ID: {result[0]}',
        f'Назва: {result[1]}',
        f'Опис: {result[2]}',
        f'Статус: {result[3]}',
        f'Виконавець: {result[4]}',
        f'Замовник: {result[5]}'
    ]))

    await state.finish()


# End --------------------------------------------------------------------------------------------------------

# Видалення задачі --------------start--------
async def enter_delete_task(message: Message):
    await message.answer("Введіть номер задачі яку Ви хочете видалити:")

    # Очікування id задачі
    await Task.waiting_for_id_task_delete.set()


async def answer_delete_task(message: Message, state: FSMContext):
    # Операції з БД
    id_task = message.text
    db = sqlite.Database()
    res = db.get_info_task(id_task)
    db.delete_task(id_task)
    await message.answer('\n'.join([
        f"ID:{res[0]}",
        f"Назва:{res[1]}",
        f"Задача була успішно видалена!"
    ]))
    await state.finish()


# End --------------------------------------------------------------------------------------------------------

# ---------------
def my_handler_wrapper(bot: Bot):
    async def my_handler(message: types.Message):
        chat_member = await bot.get_chat_member(message.chat.id, bot.id)
        if chat_member.status == types.ChatMemberStatus.ADMINISTRATOR and message.content_type == types.ContentType.TEXT:
            return  # Бот є адміністратором у чаті і повідомлення є текстовим, не потрібно реагувати

    return my_handler


# ---------------

def register_user(dp: Dispatcher, bot: Bot):
    dp.register_message_handler(user_start, commands=["start"], state="*")
    # Створення задачі
    dp.register_message_handler(enter_create_task, text="Створити задачу")
    dp.register_message_handler(answer_task_name, state=Task.waiting_for_task_name)
    dp.register_message_handler(answer_task_detail, state=Task.waiting_for_task_detail)
    # End --------------------------------------------------------------------------------------------------------
    # Надсилання в групу та опрацювання
    dp.register_callback_query_handler(enter_send_task_to_wrapper(bot), state=Task.waiting_for_send_task)
    dp.register_callback_query_handler(enter_take_task_in_group, choice_callback.filter(name='take_task'))
    dp.register_callback_query_handler(update_task_to_done, choice_callback.filter(name="done"))
    # End --------------------------------------------------------------------------------------------------------
    # Інформація про задачу
    dp.register_message_handler(enter_info_task, text="Інформація про задачу")
    dp.register_message_handler(answer_info_task, state=Task.waiting_for_id_task_detail)
    # End --------------------------------------------------------------------------------------------------------
    # Видалення задачі
    dp.register_message_handler(enter_delete_task, text="Видалити задачу")
    dp.register_message_handler(answer_delete_task, state=Task.waiting_for_id_task_delete)
    # End --------------------------------------------------------------------------------------------------------
    dp.register_message_handler(my_handler_wrapper(bot), chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
