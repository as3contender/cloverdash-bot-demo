import asyncpg
import asyncio
from typing import List, Dict, Any, Optional
import time
import logging
from contextlib import asynccontextmanager

from config.settings import settings
from models.schemas import DatabaseQueryResult

logger = logging.getLogger(__name__)


class DatabaseService:
    """Сервис для работы с базой данных"""

    def __init__(self):
        """Инициализация сервиса базы данных"""
        self.database_url = settings.get_database_url()
        self.pool: Optional[asyncpg.Pool] = None
        self._connection_status = False

        logger.info("Database Service initialized")

    async def initialize(self):
        """Инициализация пула соединений с базой данных"""
        try:
            self.pool = await asyncpg.create_pool(self.database_url, min_size=1, max_size=10, command_timeout=60)
            self._connection_status = True
            logger.info("Database connection pool created successfully")
        except Exception as e:
            self._connection_status = False
            logger.error(f"Failed to create database connection pool: {str(e)}")
            raise

    async def close(self):
        """Закрытие пула соединений"""
        if self.pool:
            await self.pool.close()
            self._connection_status = False
            logger.info("Database connection pool closed")

    @property
    def is_connected(self) -> bool:
        """Проверка статуса подключения к базе данных"""
        return self._connection_status and self.pool is not None

    async def execute_query(self, sql_query: str) -> DatabaseQueryResult:
        """
        Выполняет SQL запрос и возвращает результат

        Args:
            sql_query: SQL запрос для выполнения

        Returns:
            DatabaseQueryResult: Результат выполнения запроса
        """
        if not self.is_connected:
            raise Exception("База данных недоступна")

        start_time = time.time()

        try:
            async with self.pool.acquire() as connection:
                # Выполняем запрос
                rows = await connection.fetch(sql_query)

                execution_time = time.time() - start_time

                # Преобразуем результат в удобный формат
                if rows:
                    columns = list(rows[0].keys())
                    data = [dict(row) for row in rows]
                else:
                    columns = []
                    data = []

                result = DatabaseQueryResult(
                    data=data, columns=columns, row_count=len(data), execution_time=execution_time
                )

                logger.info(f"Query executed successfully in {execution_time:.2f}s, returned {len(data)} rows")

                return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Database query failed after {execution_time:.2f}s: {str(e)}")
            raise Exception(f"Ошибка выполнения запроса к базе данных: {str(e)}")

    async def test_connection(self) -> bool:
        """
        Тестирует подключение к базе данных

        Returns:
            bool: True если подключение успешно, False в противном случае
        """
        try:
            if not self.pool:
                return False

            async with self.pool.acquire() as connection:
                result = await connection.fetchval("SELECT 1")
                return result == 1

        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            return False

    async def get_database_schema(self) -> Dict[str, Any]:
        """
        Получает схему базы данных (список таблиц и колонок)

        Returns:
            Dict: Схема базы данных
        """
        if not self.is_connected:
            raise Exception("База данных недоступна")

        try:
            schema_query = """
            SELECT 
                table_name,
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
            """

            async with self.pool.acquire() as connection:
                rows = await connection.fetch(schema_query)

                # Группируем по таблицам
                schema = {}
                for row in rows:
                    table_name = row["table_name"]
                    if table_name not in schema:
                        schema[table_name] = []

                    schema[table_name].append(
                        {
                            "column_name": row["column_name"],
                            "data_type": row["data_type"],
                            "is_nullable": row["is_nullable"] == "YES",
                            "column_default": row["column_default"],
                        }
                    )

                logger.info(f"Retrieved schema for {len(schema)} tables")
                return schema

        except Exception as e:
            logger.error(f"Failed to retrieve database schema: {str(e)}")
            raise Exception(f"Ошибка получения схемы базы данных: {str(e)}")

    @asynccontextmanager
    async def get_connection(self):
        """
        Контекстный менеджер для получения соединения с базой данных

        Yields:
            asyncpg.Connection: Соединение с базой данных
        """
        if not self.is_connected:
            raise Exception("База данных недоступна")

        async with self.pool.acquire() as connection:
            try:
                yield connection
            except Exception as e:
                logger.error(f"Database operation failed: {str(e)}")
                raise


# Создаем глобальный экземпляр сервиса
database_service = DatabaseService()
