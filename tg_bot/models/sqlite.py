import sqlite3


class Database:
    def __init__(self, database="task.db"):
        self.database = database

    @property
    def connection(self):
        return sqlite3.connect(self.database)

    def execute(self, sql: str, parameters: tuple = None, fetchone=False, fetchall=False, commit=False):
        if not parameters:
            parameters = tuple()
        connection = self.connection
        # Loger
        # connection.set_trace_callback(logger)
        #
        cursor = connection.cursor()
        data = None

        cursor.execute(sql, parameters)

        # Команди
        if commit:
            connection.commit()
        if fetchone:
            data = cursor.fetchone()
        if fetchall:
            data = cursor.fetchall()
        connection.close()
        return data

    # Створення таблиці задач
    def create_table_task(self):
        sql = '''CREATE TABLE IF NOT EXISTS Task
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
             task_name TEXT NOT NULL,
             task_detail TEXT NOT NULL,
             status TEXT NULL,
             performer TEXT NULL,
             customer TEXT NOT NULL)'''
        self.execute(sql, commit=True)

    # Додавання в таблицю задачі
    def add_task(self, params: tuple):
        """
        :param params: task_name, task_detail, status, performer, customer
        """
        sql = """INSERT INTO Task (task_name, task_detail,status, performer, customer) VALUES (?, ?, ?, ?, ?)"""
        self.execute(sql, parameters=params, commit=True)

    #

    # Отримати останнє значення id
    def get_last_id(self):
        sql = "SELECT seq FROM sqlite_sequence WHERE name = 'Task'"
        return self.execute(sql, fetchone=True)[0]

    # Оновлення статусу
    def update_task_status(self, id_task: int, status: str):
        sql = "UPDATE Task SET status = ? WHERE id = ?"
        self.execute(sql, parameters=(status, id_task), commit=True)

    # Оновлення виконавця
    def update_task_performer(self, id_task: int, performer: str):
        sql = "UPDATE Task SET performer = ? WHERE id = ?"
        self.execute(sql, parameters=(performer, id_task), commit=True)

    # Вибір всіх задач
    def select_all_task(self):
        sql = """SELECT * FROM Task"""
        return self.execute(sql, fetchall=True)

    # Вибір задачі для отримання інформації про неї
    def get_info_task(self, id_task: int):
        sql = """SELECT * FROM Task WHERE id = ?"""
        return self.execute(sql, parameters=(id_task,), fetchone=True)

    # Видалення задачі
    def delete_task(self, id_task: int):
        sql = """DELETE FROM Task WHERE id = ?"""
        self.execute(sql, parameters=(id_task,), commit=True)


# Логування
def logger(statement):
    print(f"""
    -------------------------------------------------
    Executing:
    {statement}
    ------------------------------------------------
    """)
