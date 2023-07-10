import asyncpg.exceptions
from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message

from tg_bot.misc.states import Task2
from tg_bot.models.postgresql import Database


async def enter_start(message: Message):
    await message.answer(f"Привіт, {message.from_user.full_name}\nОбери дії зі мною:")


# Створення користувача як замовника задачі та запит на отримання назви
async def enter_create_new_task(message: Message, db: Database):
    try:
        await db.add_new_user(fullname=message.from_user.full_name, username=message.from_user.username,
                              telegram_id=message.from_user.id, role_name='Замовник')
    except asyncpg.exceptions.UniqueViolationError:
        await db.select_user(telegram_id=message.from_user.id)

    await message.answer('Надішли мені назву завдання:')
    await Task2.waiting_for_task_name.set()


# Отримання назви та запит на отримання деталей
async def answer_task_name(message: Message, state: FSMContext):
    await state.update_data(task_name=message.text)
    await message.answer("А тепер її опис:")
    await Task2.waiting_for_task_detail.set()


# Отримання деталей та формування завдання, додавання задачі в таблицю зі статусом "Очікування виконавця"
def wrapper_answer_task_detail(db: Database):
    async def answer_task_detail(message: Message, state: FSMContext):
        await message.answer('Отримав Ваші дані та формую завдання')
        # Збір информації
        # Task
        data = await state.get_data()
        task_detail = message.text
        task_id = await db.add_new_task(name=data.get('task_name'), detail=task_detail)
        # User
        user_info = await db.select_user(telegram_id=message.from_user.id)
        user_id = dict(user_info).get('id')
        # Status
        status_id = await db.get_status_id("Очікування виконавця")
        # Запис в головну таблицю
        entry_id = await db.add_new_entry_in_worksheet(task_id=task_id, user_id=user_id, status_id=status_id)
        # Отримання запису з головної таблиці
        entry = await db.select_entry(entry_id=entry_id)
        response = format_entry(entry)

        await message.answer('\n'.join([
            "Створена нова задача",
            f'{response}'
        ]))
        # Finish FSM Context
        await state.finish()

    return answer_task_detail


def format_entry(entry) -> str:
    entry_id = entry[0]
    task_name = entry[5]
    task_detail = entry[6]
    role_name = entry[11]
    customer = entry[8]
    status = entry[13]

    # Наявність елементів
    # for i in range(len(entry)):
    #     print(f'{i}: {entry[i]}')

    response = '\n'.join([
        f'Запис ID: {entry_id}',
        f'Назва: {task_name}',
        f'Опис: {task_detail}',
        f'{role_name}: {customer}',
        f'Статус: {status}'
    ])
    return response


def register_user_in_users(dp: Dispatcher, db: Database):
    dp.register_message_handler(enter_start, commands=['my_start'])
    dp.register_message_handler(lambda message: enter_create_new_task(message, db), commands="create_new_task")
    dp.register_message_handler(answer_task_name, state=Task2.waiting_for_task_name)
    dp.register_message_handler(wrapper_answer_task_detail(db), state=Task2.waiting_for_task_detail)
