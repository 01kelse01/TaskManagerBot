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

    async def create(self):
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

    async def create_table_users(self):
        sql = """
        CREATE TABLE IF NOT EXISTS Users (
        id SERIAL PRIMARY KEY,
        fullname VARCHAR(255) NOT NULL,
        username VARCHAR(255) NULL,
        telegram_id BIGINT NOT NULL UNIQUE
        );
        """
        await self.execute(sql, execute=True)

    # Додавання користувача в базу
    async def add_user(self, fullname, username, telegram_id):
        sql = "INSERT INTO Users (fullname, username, telegram_id) VALUES($1, $2, $3) returning *"
        return await self.execute(sql, fullname, username, telegram_id, fetchrow=True)

    @staticmethod
    def format_args(sql, parameters: dict):
        sql += " AND ".join([
            f'{item} = ${num}' for num, item in enumerate(parameters.keys(), start=1)
        ])
        return sql, tuple(parameters.values())

    async def select_user(self, **kwargs):
        sql = "SELECT * FROM Users WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)

    async def select_all_users(self):
        sql = "SELECT * FROM Users"
        return await self.execute(sql, fetch=True)

    async def select_count_users(self):
        sql = "SELECT COUNT(*) FROM Users"
        return await self.execute(sql, fetchval=True)

    async def drop_users(self):
        sql = "DROP TABLE Users"
        await self.execute(sql, execute=True)
