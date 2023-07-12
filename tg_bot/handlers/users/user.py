import asyncpg.exceptions
from aiogram import Dispatcher, Bot
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery

from tg_bot.keyboards.inline.callback_datas import choice_callback
from tg_bot.keyboards.inline.choice_buttons import send, take, make_done
from tg_bot.misc.states import Task2, Command
from tg_bot.models.postgresql import Database


# Просто повертає id групи яка там вказана(якщо створити нову групу потрібно вказати її id)
def get_my_group_id():
    return -1001922917876


async def enter_start(message: Message):
    await message.answer(f"Привіт, {message.from_user.full_name}\nОбери дії зі мною:")


# Створення користувача як замовника задачі та запит на отримання назви
async def enter_create_new_task(message: Message, db: Database):
    try:
        res = await db.add_customer(fullname=message.from_user.full_name, username=message.from_user.username,
                                    telegram_id=message.from_user.id, role_name='Замовник')
    except asyncpg.exceptions.UniqueViolationError:
        res = await db.select_user(table_name='Customers', telegram_id=message.from_user.id)
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
        # Збір інформації:
        # Task
        data = await state.get_data()
        task_name = data.get('task_name')
        task_detail = message.text
        task_id = await db.add_task(name=task_name, detail=task_detail)

        # Customer
        customer_info = await db.select_user(table_name="Customers", telegram_id=message.from_user.id)
        customer_id = dict(customer_info).get('id')
        customer_name = dict(customer_info).get('fullname')

        # Status
        try:
            status_id = await db.add_status(name="Очікування виконавця")
        except asyncpg.exceptions.UniqueViolationError:
            status_id = await db.get_status_id("Очікування виконавця")
        status = await db.get_status_name(status_id=status_id)

        # Запис в головну таблицю
        entry_id = await db.add_entry_in_worksheet(task_id=task_id, status_id=status_id, customer_id=customer_id)
        # Формування повідомлення для надсилання

        text_task = "\n".join([
            "Створена нова задача 👋",
            f"Запис ID: {entry_id}",
            f"Назва: {task_name}",
            f"Опис: {task_detail}",
            f"Замовник: {customer_name}",
            f"Статус: {status}"
        ])

        await message.answer(text_task, reply_markup=send)

        # Finish FSM Context
        await state.finish()

    return answer_task_detail


# Надсилання нового завдання до групи
def wrapper_enter_send_new_task(bot: Bot):
    async def enter_send_new_task(call: CallbackQuery):
        # Відправляємо задачу разом з клавіатурою у груповий чат
        task = call.message.text

        GROUP_CHAT_ID = get_my_group_id()
        await bot.send_message(GROUP_CHAT_ID, task, reply_markup=take)
        # -------------------------------------------------------
        await call.message.edit_reply_markup()
        await call.message.answer("Задача надіслана!")

    return enter_send_new_task


# Натискання на кнопку "взяти в роботу"
async def enter_take_new_task(call: CallbackQuery, db: Database):
    # Отримання даних від виконавця
    full_name = call.from_user.full_name
    username = call.from_user.username
    telegram_id = call.from_user.id
    role_name = "Виконавець"

    # Додавання виконавця в таблицю
    try:
        performer_id = await db.add_performer(full_name, username, telegram_id, role_name)
    except asyncpg.exceptions.UniqueViolationError:
        tmp_record = await db.select_user(table_name='Performers', telegram_id=telegram_id)
        performer_id = tmp_record['id']

    # Отримання ID запису з повідомлення
    entry_id = int(call.message.text.split('\n')[1].split(":")[1])  # str -> int

    # Додавання статусу та отримання його id та name
    try:
        status_taken_id = await db.add_status(name='В роботі')
    except asyncpg.exceptions.UniqueViolationError:
        status_taken_id = await db.get_status_id(name="В роботі")
    status = await db.get_status_name(status_id=status_taken_id)

    # Оновлення запису в worksheet
    await db.update_entry_in_worksheet(entry_id=entry_id, status_id=status_taken_id, performer_id=performer_id)

    # Генерація оновлення повідомлення
    new_text = await format_text(call.message.text)
    my_text = '\n'.join([
        f'{new_text}',
        f'Статус: {status}',
        f'Виконавець: {full_name}'
    ])
    await call.message.edit_text(text=my_text)
    await call.message.edit_reply_markup(reply_markup=make_done)
    await call.answer("Задачу взято в роботу!")


# ------------------------------------------------------------------------------------------------
async def format_text(text: str) -> str:
    list_text = text.split('\n')
    result = '\n'.join([
        f'{list_text[1]}',
        f'{list_text[2]}',
        f'{list_text[3]}',
        f'{list_text[4]}'
    ])
    return result


async def check_performer(db: Database, entry_id: int, telegram_id: int):
    performer = await db.select_user(table_name='Performers', telegram_id=telegram_id)
    performer_id = dict(performer).get('id')
    print('id', performer_id)
    entry = await db.select_entry(entry_id=entry_id)
    print('entry', entry)


# ------------------------------------------------------------------------------------------------

async def enter_make_done(call: CallbackQuery, db: Database):
    # Отримання ID виконавця через telegram_id
    performer = await db.select_user(table_name="Performers", telegram_id=call.from_user.id)
    performer_id = dict(performer).get('id')
    full_name = dict(performer).get('fullname')

    # Отримання ID запису з повідомлення
    entry_id = int(call.message.text.split('\n')[0].split(":")[1])  # str -> int
    
    # Додавання статусу та отримання його id та name
    try:
        status_taken_id = await db.add_status(name='Виконано')
    except asyncpg.exceptions.UniqueViolationError:
        status_taken_id = await db.get_status_id(name="Виконано")
    status = await db.get_status_name(status_id=status_taken_id)

    # await check_performer(db=db,)

    # Оновлення запису в worksheet
    await db.update_entry_in_worksheet(entry_id=entry_id, status_id=status_taken_id, performer_id=performer_id)

    # Генерація оновлення повідомлення
    new_text = call.message.text.split('\n')
    my_text = '\n'.join([
        f'{new_text[0]}',
        f'{new_text[1]}',
        f'{new_text[2]}',
        f'{new_text[3]}',
        f'Статус: {status}',
        f'Виконавець: {full_name}'
    ])
    await call.message.edit_text(text=my_text)
    await call.answer('Ви виконали завдання')


def register_user_in_users(dp: Dispatcher, db: Database, bot: Bot):
    dp.register_message_handler(enter_start, commands=['my_start'])
    dp.register_message_handler(lambda message: enter_create_new_task(message, db), commands="create_new_task")
    dp.register_message_handler(answer_task_name, state=Task2.waiting_for_task_name)
    dp.register_message_handler(wrapper_answer_task_detail(db), state=Task2.waiting_for_task_detail)
    #
    dp.register_callback_query_handler(wrapper_enter_send_new_task(bot), choice_callback.filter(name='send_new_task'))
    dp.register_callback_query_handler(lambda call: enter_take_new_task(call, db),
                                       choice_callback.filter(name='take_new_task'))
    #
    dp.register_callback_query_handler(lambda call: enter_make_done(call, db), choice_callback.filter(name='done_task'))
