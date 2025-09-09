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
                
                # Парсим JSON строку если нужно
                if isinstance(description, str):
                    try:
                        import json
                        description = json.loads(description)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse JSON description for {database_name}.{schema_name}.{table_name}")
                        return None
                
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

    async def get_user_accessible_tables(self, user_id: str, database_name: str) -> List[Dict[str, Any]]:
        """Получение списка доступных таблиц для пользователя из database_descriptions
        с учетом прав пользователя из user_permissions (если таблица существует)"""
        try:
            # Сначала проверяем, существует ли таблица user_permissions
            permissions_exist = await self._check_user_permissions_table_exists()

            if permissions_exist:
                # Если таблица прав существует, получаем таблицы с учетом прав через role_name
                query = """
                SELECT DISTINCT 
                    dd.database_name,
                    dd.schema_name,
                    dd.table_name,
                    dd.object_type,
                    dd.table_description,
                    dd.created_at,
                    dd.updated_at
                FROM database_descriptions dd
                INNER JOIN user_permissions tp 
                 inner join users_role_bd_mapping um on tp.role_name = um.role_name and um.user_id = $1
                ON
                    dd.database_name = tp.database_name AND
                    dd.schema_name = tp.schema_name AND
                    dd.table_name = tp.table_name
               WHERE dd.database_name = $2
                """

                result = await self.execute_query(query, [user_id, database_name])
            else:
                # Если таблицы прав нет, возвращаем все таблицы
                query = """
                SELECT 
                    database_name,
                    schema_name,
                    table_name,
                    object_type,
                    table_description,
                    created_at,
                    updated_at
                FROM database_descriptions
                WHERE database_name = $1
                ORDER BY schema_name, table_name
                """

                result = await self.execute_query(query, [database_name])

            # Форматируем результат
            tables = []
            for row in result.data:
                table_info = {
                    "full_name": f"{row['schema_name']}.{row['table_name']}",
                    "schema_name": row["schema_name"],
                    "table_name": row["table_name"],
                    "object_type": row["object_type"],
                    "description": row["table_description"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                }
                tables.append(table_info)

            logger.info(f"Found {len(tables)} accessible tables for user {user_id} in database {database_name}")
            return tables

        except Exception as e:
            logger.error(f"Failed to get accessible tables for user {user_id}: {str(e)}")
            return []

    async def _check_user_permissions_table_exists(self) -> bool:
        """Проверяет, существует ли таблица user_permissions для разрешений на конкретные таблицы"""
        try:
            query = """
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'user_permissions'
            """

            result = await self.execute_query(query)
            exists = result.data and result.data[0]["count"] > 0

            if exists:
                logger.info("User permissions table found - using permission-based access")
            else:
                logger.info("User permissions table not found - allowing access to all tables")

            return exists

        except Exception as e:
            logger.warning(f"Error checking user permissions table: {str(e)}")
            return False

    async def get_database_schema(
        self, database_name: str, include_views: bool = True, schema_name: str = "public"
    ) -> Dict[str, Any]:
        """Получение схемы базы данных из database_descriptions"""
        try:
            schema = {}

            # Получаем все описания из database_descriptions
            if schema_name is None:
                saved_descriptions = await self.get_all_table_descriptions(database_name=database_name)
            else:
                saved_descriptions = await self.get_all_table_descriptions(
                    database_name=database_name, schema_name=schema_name
                )

            logger.info(f"Found {len(saved_descriptions)} descriptions in database_descriptions")

            # Строим схему на основе сохраненных описаний
            for key, description in saved_descriptions.items():
                # key format: "database.schema.table"
                parts = key.split(".")
                if len(parts) >= 3:
                    table_name = parts[-1]  # последняя часть - имя таблицы
                    table_schema = parts[-2]  # предпоследняя - схема

                    # Парсим JSON если description - строка
                    if isinstance(description, str):
                        try:
                            description = json.loads(description)
                        except (json.JSONDecodeError, TypeError):
                            logger.warning(f"Failed to parse description JSON for {key}: {description}")
                            description = {"description": str(description)}

                    object_type = description.get("object_type", "table")

                    # Фильтруем представления если нужно
                    if not include_views and object_type == "view":
                        continue

                    # Фильтруем по схеме если указана
                    if schema_name is not None and table_schema != schema_name:
                        continue

                    schema[table_name] = {
                        "columns": [],
                        "description": description.get("description", f"User data {object_type}"),
                        "object_type": object_type,
                        "schema_name": table_schema,
                    }

                    # Добавляем колонки из описания
                    if "columns" in description:
                        columns_desc = description["columns"]
                        for col_name, col_info in columns_desc.items():
                            if isinstance(col_info, dict):
                                # Полная информация о колонке из column_descriptions.json
                                column_data = {
                                    "name": col_name,
                                    "description": col_info.get("описание", ""),
                                    "datatype": col_info.get("datatype", "character varying"),
                                    "type": col_info.get("datatype", "character varying"),
                                    "placeholder": col_info.get("placeholder", ""),
                                    "tags": col_info.get("теги", ""),
                                    "nullable": True,  # по умолчанию
                                    "default": None,
                                }
                            else:
                                # Простое описание как строка
                                column_data = {
                                    "name": col_name,
                                    "description": str(col_info),
                                    "datatype": "character varying",
                                    "type": "character varying",
                                    "nullable": True,
                                    "default": None,
                                }

                            schema[table_name]["columns"].append(column_data)

            tables_count = sum(1 for v in schema.values() if v.get("object_type") == "table")
            views_count = sum(1 for v in schema.values() if v.get("object_type") == "view")
            schema_info = "all schemas" if schema_name is None else f"{schema_name} schema"

            logger.info(f"Retrieved schema from {schema_info}: {tables_count} tables, {views_count} views")
            logger.info(f"All objects loaded from database_descriptions (curated data)")

            return schema

        except Exception as e:
            logger.error(f"Failed to get database schema: {str(e)}")
            raise Exception(f"Schema retrieval failed: {str(e)}")

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

    async def get_database_schema_with_user_permissions(
        self, 
        user_id: str, 
        database_name: str, 
        include_views: bool = True, 
        schema_name: str = "public"
    ) -> Dict[str, Any]:
        """Получение схемы БД с учетом прав пользователя"""
        try:
            schema = {}

            # Получаем все описания из database_descriptions
            if schema_name is None:
                saved_descriptions = await self.get_all_table_descriptions(database_name=database_name)
            else:
                saved_descriptions = await self.get_all_table_descriptions(
                    database_name=database_name, schema_name=schema_name
                )

            logger.info(f"Found {len(saved_descriptions)} descriptions in database_descriptions")

            # ФИЛЬТРУЕМ по правам пользователя
            filtered_descriptions = await self._filter_descriptions_by_user_permissions(
                saved_descriptions, user_id, database_name
            )

            logger.info(f"Found {len(filtered_descriptions)} accessible descriptions for user {user_id}")

            # Строим схему на основе отфильтрованных описаний
            for key, description in filtered_descriptions.items():
                # key format: "database.schema.table"
                parts = key.split(".")
                if len(parts) >= 3:
                    table_name = parts[-1]  # последняя часть - имя таблицы
                    table_schema = parts[-2]  # предпоследняя - схема

                    # Парсим JSON если description - строка
                    if isinstance(description, str):
                        try:
                            description = json.loads(description)
                        except (json.JSONDecodeError, TypeError):
                            logger.warning(f"Failed to parse description JSON for {key}: {description}")
                            description = {"description": str(description)}

                    object_type = description.get("object_type", "table")

                    # Фильтруем представления если нужно
                    if not include_views and object_type == "view":
                        continue

                    # Фильтруем по схеме если указана
                    if schema_name is not None and table_schema != schema_name:
                        continue

                    schema[table_name] = {
                        "columns": [],
                        "description": description.get("description", f"User data {object_type}"),
                        "object_type": object_type,
                        "schema_name": table_schema,
                    }

                    # Добавляем колонки из описания
                    if "columns" in description:
                        columns_desc = description["columns"]
                        for col_name, col_info in columns_desc.items():
                            if isinstance(col_info, dict):
                                # Полная информация о колонке из column_descriptions.json
                                column_data = {
                                    "name": col_name,
                                    "description": col_info.get("описание", ""),
                                    "datatype": col_info.get("datatype", "character varying"),
                                    "type": col_info.get("datatype", "character varying"),
                                    "placeholder": col_info.get("placeholder", ""),
                                    "tags": col_info.get("теги", ""),
                                    "nullable": True,  # по умолчанию
                                    "default": None,
                                }
                            else:
                                # Простое описание как строка
                                column_data = {
                                    "name": col_name,
                                    "description": str(col_info),
                                    "datatype": "character varying",
                                    "type": "character varying",
                                    "nullable": True,
                                    "default": None,
                                }

                            schema[table_name]["columns"].append(column_data)

            tables_count = sum(1 for v in schema.values() if v.get("object_type") == "table")
            views_count = sum(1 for v in schema.values() if v.get("object_type") == "view")
            schema_info = "all schemas" if schema_name is None else f"{schema_name} schema"

            logger.info(f"Retrieved schema with user permissions from {schema_info}: {tables_count} tables, {views_count} views")
            logger.info(f"User {user_id} has access to {len(schema)} objects from database_descriptions")

            return schema

        except Exception as e:
            logger.error(f"Failed to get database schema with user permissions: {str(e)}")
            raise Exception(f"Schema retrieval with user permissions failed: {str(e)}")

    async def _filter_descriptions_by_user_permissions(
        self, 
        descriptions: Dict[str, Any], 
        user_id: str, 
        database_name: str
    ) -> Dict[str, Any]:
        """Фильтрует описания таблиц по правам пользователя"""
        try:
            # Получаем доступные таблицы для пользователя
            accessible_tables = await self.get_user_accessible_tables(user_id, database_name)
            
            # Создаем множество доступных таблиц
            accessible_set = set()
            for table in accessible_tables:
                key = f"{table['schema_name']}.{table['table_name']}"
                accessible_set.add(key)
            
            logger.info(f"User {user_id} has access to {len(accessible_set)} tables: {list(accessible_set)}")
            
            # Фильтруем описания
            filtered = {}
            for key, description in descriptions.items():
                # key format: "database.schema.table"
                parts = key.split(".")
                if len(parts) >= 3:
                    table_key = f"{parts[-2]}.{parts[-1]}"  # schema.table
                    if table_key in accessible_set:
                        filtered[key] = description
                        logger.info(f"✅ Added {key} to filtered descriptions")
                    else:
                        logger.info(f"❌ Skipped {key} - not in accessible set")
            
            logger.info(f"Filtered {len(descriptions)} descriptions to {len(filtered)} accessible for user {user_id}")
            return filtered
            
        except Exception as e:
            logger.error(f"Failed to filter descriptions by user permissions: {str(e)}")
            return descriptions  # Возвращаем все в случае ошибки


# Создаем глобальный экземпляр сервиса
app_database_service = AppDatabaseService()
