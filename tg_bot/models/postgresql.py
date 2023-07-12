from typing import Union

import asyncpg
from aiogram import Bot
from asyncpg import Pool, Connection


def get_my_config(bot: Bot):
    return bot['config']


class Database:
    def __init__(self, bot: Bot):
        self.pool: Union[Pool, None] = None
        self.config = get_my_config(bot)

    # Створення пулу з'єднання
    async def create(self):
        """Create pool"""
        self.pool = await asyncpg.create_pool(
            user=self.config.db.user,
            password=self.config.db.password,
            host=self.config.db.host,
            database=self.config.db.database
        )

    async def execute(self, command, *args,
                      fetch: bool = False,
                      fetchval: bool = False,
                      fetchrow: bool = False,
                      execute: bool = False):
        async with self.pool.acquire() as connection:
            connection: Connection
            async with connection.transaction():
                if fetch:
                    result = await connection.fetch(command, *args)
                elif fetchval:
                    result = await connection.fetchval(command, *args)
                elif fetchrow:
                    result = await connection.fetchrow(command, *args)
                elif execute:
                    result = await connection.execute(command, *args)
            return result

    # Форматування запиту
    @staticmethod
    def format_args(sql, parameters: dict):
        sql += " AND ".join([
            f'{item} = ${num}' for num, item in enumerate(parameters.keys(), start=1)
        ])
        return sql, tuple(parameters.values())

    # ---------------------------------------------------------------------------------------------------------
    # TODO: Створення таблиць

    async def create_table_customers(self):
        sql = """
            CREATE TABLE IF NOT EXISTS Customers (
            id SERIAL PRIMARY KEY, 
            fullname VARCHAR(100) NULL, 
            username VARCHAR(50) NULL, 
            telegram_id BIGINT NOT NULL UNIQUE, 
            role_name VARCHAR(255) NULL
            );
        """
        await self.execute(sql, execute=True)

    async def create_table_performers(self):
        sql = """
            CREATE TABLE IF NOT EXISTS Performers (
            id SERIAL PRIMARY KEY, 
            fullname VARCHAR(100) NULL, 
            username VARCHAR(50) NULL, 
            telegram_id BIGINT NOT NULL UNIQUE, 
            role_name VARCHAR(255) NULL
            );
        """
        await self.execute(sql, execute=True)

    async def create_table_tasks(self):
        sql = """
            CREATE TABLE IF NOT EXISTS Tasks (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NULL,
            detail TEXT NULL
            );
        """
        await self.execute(sql, execute=True)

    async def create_table_status(self):
        sql = """
            CREATE TABLE IF NOT EXISTS Status (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) NULL UNIQUE
            );
        """
        await self.execute(sql, execute=True)

    async def create_table_worksheet(self):
        sql = """
                CREATE TABLE IF NOT EXISTS Worksheet (
                id SERIAL PRIMARY KEY,
                task_id INT NOT NULL REFERENCES Tasks (id),
                status_id INT NOT NULL REFERENCES Status (id),
                customer_id INT NOT NULL REFERENCES Customers (id),
                performer_id INT NULL REFERENCES Performers (id)
                );
            """
        await self.execute(sql, execute=True)

    async def create_all_tables(self):
        """Create all tables in Database"""
        await self.create_table_customers()
        await self.create_table_performers()
        await self.create_table_tasks()
        await self.create_table_status()
        await self.create_table_worksheet()

    # TODO: Додавання в таблиці інформацію
    async def add_customer(self, fullname: str, username: str, telegram_id: int, role_name: str) -> int:
        sql = "INSERT INTO Customers (fullname, username, telegram_id, role_name) VALUES($1, $2, $3, $4) returning id"
        return await self.execute(sql, fullname, username, telegram_id, role_name, fetchval=True)

    async def add_performer(self, fullname: str, username: str, telegram_id: int, role_name: str) -> int:
        sql = "INSERT INTO Performers (fullname, username, telegram_id, role_name) VALUES($1, $2, $3, $4) returning id"
        return await self.execute(sql, fullname, username, telegram_id, role_name, fetchval=True)

    async def add_task(self, name: str, detail: str) -> int:
        sql = "INSERT INTO Tasks (name, detail) VALUES ($1, $2) returning id"
        return await self.execute(sql, name, detail, fetchval=True)

    async def add_status(self, name: str) -> int:
        sql = "INSERT INTO Status (name) VALUES ($1) returning id"
        return await self.execute(sql, name, fetchval=True)

    async def add_entry_in_worksheet(self, task_id: int, status_id: int, customer_id: int) -> int:
        sql = """
            INSERT INTO Worksheet (task_id, status_id, customer_id) VALUES ($1, $2, $3) returning id
        """
        return await self.execute(sql, task_id, status_id, customer_id, fetchval=True)

    # TODO: Перегляд даних з таблиць
    async def select_user(self, table_name: str, **kwargs):
        sql = f"SELECT * FROM {table_name} WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)

    async def select_entry(self, entry_id: int) -> object:
        sql = """
               SELECT *
               FROM Worksheet
               JOIN Tasks ON Worksheet.task_id = Tasks.id
               JOIN Status ON Worksheet.status_id = Status.id
               JOIN Customers ON Worksheet.customer_id_id = Customers.id
               JOIN Performers ON Worksheet.performer_id = Performers.id
               WHERE Worksheet.id = $1
           """
        return await self.execute(sql, entry_id, fetchrow=True)

    # TODO: Отримання даних з таблиць
    async def get_status_id(self, name) -> int:
        sql = "SELECT id FROM Status WHERE name = $1"
        return await self.execute(sql, name, fetchval=True)

    async def get_status_name(self, status_id: int) -> str:
        sql = 'SELECT name FROM Status WHERE id = $1'
        return await self.execute(sql, status_id, fetchval=True)

    # TODO: Оновлення даних в таблицях
    async def update_entry_in_worksheet(self, entry_id: int, status_id: int, performer_id: int, ):
        sql = """
                UPDATE Worksheet
                SET status_id = $1,
                    performer_id = $2

                WHERE id = $3;
            """
        await self.execute(sql, status_id, performer_id, entry_id, execute=True)

    # ---------------------------------------------------------------------------------------------------------
    # # Створення таблиці користувачів
    # async def create_table_users(self):
    #     sql = """
    #         CREATE TABLE IF NOT EXISTS Users (
    #         id SERIAL PRIMARY KEY,
    #         fullname VARCHAR(255) NOT NULL,
    #         username VARCHAR(255) NULL,
    #         telegram_id BIGINT NOT NULL UNIQUE,
    #         role_name VARCHAR(50) NULL
    #         );
    #     """
    #     await self.execute(sql, execute=True)
    #
    # # Створення таблиці задач
    # async def create_table_tasks(self):
    #     sql = '''
    #         CREATE TABLE IF NOT EXISTS Task
    #          (id INTEGER PRIMARY KEY AUTOINCREMENT,
    #          task_name TEXT NOT NULL,
    #          task_detail TEXT NOT NULL,
    #          status TEXT NULL,
    #          performer TEXT NULL,
    #          customer TEXT NULL
    #          );
    #      '''
    #     await self.execute(sql, execute=True)
    #
    # # Створення зв'язку між таблицями Users and Tasks
    # async def users_tasks(self):
    #     sql = """
    #         CREATE TABLE Users_Task (
    #         user_id INTEGER REFERENCES Users(id),
    #         task_id INTEGER REFERENCES Task(id),
    #         PRIMARY KEY (user_id, task_id)
    #     """
    #     await self.execute(sql, execute=True)

    # Додавання користувача в базу
    # async def add_user(self, fullname, username, telegram_id, role_name):
    #     sql = """
    #         INSERT INTO Users (fullname, username, telegram_id, role_name)
    #         VALUES($1, $2, $3, $4) returning *
    #         """
    #     return await self.execute(sql, fullname, username, telegram_id, role_name, fetchrow=True)
    #
    # async def add_task(self, task_name, task_detail, status, performer, customer):
    #     sql = """
    #         INSERT INTO Task (task_name, task_detail, status, performer, customer)
    #         VALUES ($1, $2, $3, $4, $5) returning *
    #         """
    #     return await self.execute(sql, task_name, task_detail, status, performer, customer, fetchrow=True)

    # async def select_count_users(self):
    #     sql = "SELECT COUNT(*) FROM Users"
    #     return await self.execute(sql, fetchval=True)
