import asyncpg
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from config.settings import settings
from models.database import DatabaseQueryResult

logger = logging.getLogger(__name__)


class AppDatabaseService:
    """Сервис для работы с базой данных приложения (пользователи, история, настройки)"""

    def __init__(self):
        self.pool = None
        self.is_connected = False

    async def initialize(self):
        """Инициализация подключения к базе данных приложения"""
        try:
            database_url = settings.get_app_database_url()

            self.pool = await asyncpg.create_pool(database_url, min_size=1, max_size=10, command_timeout=60)

            # Тестируем подключение
            async with self.pool.acquire() as connection:
                await connection.fetchval("SELECT 1")

            self.is_connected = True
            logger.info("Application database connection established")

        except Exception as e:
            logger.error(f"Failed to connect to application database: {str(e)}")
            self.is_connected = False
            raise

    async def close(self):
        """Закрытие подключения к базе данных"""
        if self.pool:
            await self.pool.close()
            self.is_connected = False
            logger.info("Application database connection closed")

    async def test_connection(self) -> bool:
        """Тестирование подключения к базе данных"""
        try:
            if not self.pool:
                return False

            async with self.pool.acquire() as connection:
                await connection.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Application database connection test failed: {str(e)}")
            return False

    async def execute_query(self, query: str, params: List[Any] = None) -> DatabaseQueryResult:
        """Выполнение SQL запроса в базе данных приложения"""
        if not self.is_connected or not self.pool:
            raise Exception("Application database is not connected")

        start_time = datetime.now()

        try:
            async with self.pool.acquire() as connection:
                if params:
                    result = await connection.fetch(query, *params)
                else:
                    result = await connection.fetch(query)

                # Преобразуем результат в список словарей
                data = []
                columns = []

                if result:
                    columns = list(result[0].keys())
                    for row in result:
                        data.append(dict(row))

                execution_time = (datetime.now() - start_time).total_seconds()

                return DatabaseQueryResult(
                    data=data, columns=columns, row_count=len(data), execution_time=execution_time
                )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Application database query failed: {str(e)}")
            raise Exception(f"Query execution failed: {str(e)}")

    async def save_query_history(
        self,
        user_id: str,
        query: str,
        sql_query: str,
        result_count: int,
        execution_time: float,
        success: bool,
        error_message: Optional[str] = None,
    ):
        """Сохранение истории запросов пользователя"""
        try:
            insert_query = """
            INSERT INTO query_history 
            (user_id, original_query, sql_query, result_count, execution_time, success, error_message, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """

            await self.execute_query(
                insert_query,
                [user_id, query, sql_query, result_count, execution_time, success, error_message, datetime.now()],
            )

            logger.info(f"Query history saved for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to save query history: {str(e)}")
            # Не поднимаем исключение, чтобы не нарушать основной флоу

    async def get_user_query_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение истории запросов пользователя"""
        try:
            query = """
            SELECT original_query, sql_query, result_count, execution_time, 
                   success, error_message, created_at
            FROM query_history 
            WHERE user_id = $1 
            ORDER BY created_at DESC 
            LIMIT $2
            """

            result = await self.execute_query(query, [user_id, limit])
            return result.data

        except Exception as e:
            logger.error(f"Failed to get user query history: {str(e)}")
            return []

    async def save_table_description(
        self,
        database_name: str,
        table_name: str,
        description: Dict[str, Any],
        schema_name: str = "public",
        object_type: str = "table",
    ) -> bool:
        """Сохранение описания таблицы или представления"""
        try:
            query = """
            INSERT INTO database_descriptions (database_name, schema_name, table_name, object_type, table_description, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (database_name, schema_name, table_name)
            DO UPDATE SET 
                object_type = EXCLUDED.object_type,
                table_description = EXCLUDED.table_description,
                updated_at = EXCLUDED.updated_at
            """

            description_json = json.dumps(description, ensure_ascii=False)

            await self.execute_query(
                query, [database_name, schema_name, table_name, object_type, description_json, datetime.now()]
            )

            logger.info(f"{object_type.capitalize()} description saved: {database_name}.{schema_name}.{table_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to save {object_type} description: {str(e)}")
            return False

    async def get_table_description(
        self, database_name: str, table_name: str, schema_name: str = "public"
    ) -> Optional[Dict[str, Any]]:
        """Получение описания таблицы или представления"""
        try:
            query = """
            SELECT table_description, object_type
            FROM database_descriptions 
            WHERE database_name = $1 AND schema_name = $2 AND table_name = $3
            """

            result = await self.execute_query(query, [database_name, schema_name, table_name])
            if result.data:
                description = result.data[0]["table_description"]
                # Добавляем информацию о типе объекта в описание
                if isinstance(description, dict):
                    description["object_type"] = result.data[0]["object_type"]
                return description
            return None

        except Exception as e:
            logger.error(f"Failed to get table description: {str(e)}")
            return None

    async def get_all_table_descriptions(
        self, database_name: Optional[str] = None, schema_name: Optional[str] = None, object_type: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Получение всех описаний таблиц и представлений"""
        try:
            # Строим запрос в зависимости от параметров
            conditions = []
            params = []

            if database_name:
                conditions.append("database_name = $" + str(len(params) + 1))
                params.append(database_name)

            if schema_name:
                conditions.append("schema_name = $" + str(len(params) + 1))
                params.append(schema_name)

            if object_type:
                conditions.append("object_type = $" + str(len(params) + 1))
                params.append(object_type)

            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

            query = f"""
            SELECT database_name, schema_name, table_name, object_type, table_description
            FROM database_descriptions 
            {where_clause}
            ORDER BY database_name, schema_name, object_type, table_name
            """

            result = await self.execute_query(query, params)

            descriptions = {}
            for row in result.data:
                key = f"{row['database_name']}.{row['schema_name']}.{row['table_name']}"
                description = row["table_description"]
                # Добавляем метаинформацию
                if isinstance(description, dict):
                    description["object_type"] = row["object_type"]
                    description["schema_name"] = row["schema_name"]
                descriptions[key] = description

            return descriptions

        except Exception as e:
            logger.error(f"Failed to get table descriptions: {str(e)}")
            return {}

    async def delete_table_description(self, database_name: str, table_name: str, schema_name: str = "public") -> bool:
        """Удаление описания таблицы или представления"""
        try:
            query = """
            DELETE FROM database_descriptions 
            WHERE database_name = $1 AND schema_name = $2 AND table_name = $3
            """

            await self.execute_query(query, [database_name, schema_name, table_name])
            logger.info(f"Object description deleted: {database_name}.{schema_name}.{table_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete object description: {str(e)}")
            return False

    async def create_app_tables(self):
        """Создание таблиц приложения"""
        try:
            # Таблица пользователей
            users_table = """
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                username VARCHAR(100) UNIQUE,
                email VARCHAR(255) UNIQUE,
                full_name VARCHAR(255),
                hashed_password VARCHAR(255),
                telegram_id VARCHAR(100) UNIQUE,
                telegram_username VARCHAR(100),
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """

            users_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
                "CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)",
                "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            ]

            # Таблица истории запросов
            query_history_table = """
            CREATE TABLE IF NOT EXISTS query_history (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL,
                original_query TEXT NOT NULL,
                sql_query TEXT,
                result_count INTEGER DEFAULT 0,
                execution_time FLOAT DEFAULT 0.0,
                success BOOLEAN DEFAULT false,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """

            query_history_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_query_history_user_id ON query_history(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_query_history_created_at ON query_history(created_at)",
            ]

            # Таблица настроек пользователей
            user_settings_table = """
            CREATE TABLE IF NOT EXISTS user_settings (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL UNIQUE,
                preferred_language VARCHAR(10) DEFAULT 'en',
                timezone VARCHAR(50) DEFAULT 'UTC',
                query_limit INTEGER DEFAULT 100,
                settings_json JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """

            user_settings_indexes = ["CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id)"]

            # Таблица разрешений пользователей
            user_permissions_table = """
            CREATE TABLE IF NOT EXISTS user_permissions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL,
                permission_name VARCHAR(100) NOT NULL,
                granted BOOLEAN DEFAULT true,
                granted_by UUID,
                granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (granted_by) REFERENCES users(id) ON DELETE SET NULL,
                UNIQUE(user_id, permission_name)
            )
            """

            user_permissions_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_user_permissions_user_id ON user_permissions(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_user_permissions_permission ON user_permissions(permission_name)",
            ]

            # Таблица описаний баз данных и таблиц
            database_descriptions_table = """
            CREATE TABLE IF NOT EXISTS database_descriptions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                database_name VARCHAR(255) NOT NULL,
                schema_name VARCHAR(255) NOT NULL DEFAULT 'public',
                table_name VARCHAR(255) NOT NULL,
                object_type VARCHAR(50) NOT NULL DEFAULT 'table',
                table_description JSONB NOT NULL DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(database_name, schema_name, table_name)
            )
            """

            database_descriptions_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_database_descriptions_database ON database_descriptions(database_name)",
                "CREATE INDEX IF NOT EXISTS idx_database_descriptions_schema ON database_descriptions(schema_name)",
                "CREATE INDEX IF NOT EXISTS idx_database_descriptions_table ON database_descriptions(table_name)",
                "CREATE INDEX IF NOT EXISTS idx_database_descriptions_type ON database_descriptions(object_type)",
                "CREATE INDEX IF NOT EXISTS idx_database_descriptions_combined ON database_descriptions(database_name, schema_name, table_name)",
            ]

            # Выполняем создание таблиц и индексов по отдельности
            await self.execute_query(users_table)
            for index_query in users_indexes:
                await self.execute_query(index_query)

            await self.execute_query(query_history_table)
            for index_query in query_history_indexes:
                await self.execute_query(index_query)

            await self.execute_query(user_settings_table)
            for index_query in user_settings_indexes:
                await self.execute_query(index_query)

            await self.execute_query(user_permissions_table)
            for index_query in user_permissions_indexes:
                await self.execute_query(index_query)

            await self.execute_query(database_descriptions_table)
            for index_query in database_descriptions_indexes:
                await self.execute_query(index_query)

            logger.info("Application database tables created successfully")

        except Exception as e:
            logger.error(f"Failed to create application tables: {str(e)}")
            raise


# Создаем глобальный экземпляр сервиса
app_database_service = AppDatabaseService()
