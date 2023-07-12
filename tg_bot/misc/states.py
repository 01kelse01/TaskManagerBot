from aiogram.dispatcher.filters.state import State, StatesGroup


class Task(StatesGroup):
    # Очікування назви завдання
    waiting_for_task_name = State()

    # Очікування деталей завдання
    waiting_for_task_detail = State()

    # Очікування відправки
    waiting_for_send_task = State()

    # Очікування id задачі для отримання деталей про неї
    waiting_for_id_task_detail = State()

    # Очікування id задачі для видалення
    waiting_for_id_task_delete = State()


class Command(StatesGroup):
    # Очікування команди
    waiting_command = State()


class Task2(StatesGroup):
    # Очікування назви завдання
    waiting_for_task_name = State()

    # Очікування деталей завдання
    waiting_for_task_detail = State()

    # Очікування натискання take_new_task
    waiting_take_new_task = State()
