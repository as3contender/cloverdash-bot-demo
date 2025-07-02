import asyncpg
import logging
from typing import Dict, Any, List
from datetime import datetime
import json

from config.settings import settings, DB_SCHEMA_CONTEXT
from models.database import DatabaseQueryResult

logger = logging.getLogger(__name__)


class DataDatabaseService:
    """Сервис для работы с базой данных пользовательских данных (только чтение)"""

    def __init__(self):
        self.pool = None
        self.is_connected = False
        self._database_name = None

    async def initialize(self):
        """Инициализация подключения к базе данных пользовательских данных"""
        try:
            database_url = settings.get_data_database_url()

            # Извлекаем имя базы данных из URL для использования в описаниях
            if database_url:
                self._database_name = database_url.split("/")[-1]

            self.pool = await asyncpg.create_pool(database_url, min_size=1, max_size=10, command_timeout=60)

            # Тестируем подключение
            async with self.pool.acquire() as connection:
                await connection.fetchval("SELECT 1")

            self.is_connected = True
            logger.info("Data database connection established")

        except Exception as e:
            logger.error(f"Failed to connect to data database: {str(e)}")
            self.is_connected = False
            raise

    async def close(self):
        """Закрытие подключения к базе данных"""
        if self.pool:
            await self.pool.close()
            self.is_connected = False
            logger.info("Data database connection closed")

    async def test_connection(self) -> bool:
        """Тестирование подключения к базе данных"""
        try:
            if not self.pool:
                return False

            async with self.pool.acquire() as connection:
                await connection.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Data database connection test failed: {str(e)}")
            return False

    async def execute_query(self, query: str) -> DatabaseQueryResult:
        """
        Выполнение SQL запроса в базе данных пользовательских данных
        Только SELECT запросы для безопасности
        """
        if not self.is_connected or not self.pool:
            raise Exception("Data database is not connected")

        # Проверяем, что это SELECT запрос
        query_upper = query.upper().strip()
        if not query_upper.startswith("SELECT"):
            raise Exception("Only SELECT queries are allowed for data database")

        start_time = datetime.now()

        try:
            async with self.pool.acquire() as connection:
                result = await connection.fetch(query)

                # Преобразуем результат в список словарей
                data = []
                columns = []

                if result:
                    columns = list(result[0].keys())
                    for row in result:
                        data.append(dict(row))

                execution_time = (datetime.now() - start_time).total_seconds()

                logger.info(f"Data query executed successfully: {len(data)} rows in {execution_time:.2f}s")

                return DatabaseQueryResult(
                    data=data, columns=columns, row_count=len(data), execution_time=execution_time
                )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Data database query failed: {str(e)}")
            raise Exception(f"Query execution failed: {str(e)}")

    async def get_database_schema(self, include_views: bool = True, schema_name: str = "public") -> Dict[str, Any]:
        """Получение схемы базы данных пользовательских данных с описаниями"""
        if not self.is_connected or not self.pool:
            raise Exception("Data database is not connected")

        try:
            # Импортируем здесь, чтобы избежать циклических импортов
            from services.app_database import app_database_service

            schema = {}

            # ОСНОВНОЙ ИСТОЧНИК: database_descriptions
            if app_database_service.is_connected:
                # Получаем все описания из database_descriptions
                if schema_name is None:
                    saved_descriptions = await app_database_service.get_all_table_descriptions(
                        database_name=self._database_name
                    )
                else:
                    saved_descriptions = await app_database_service.get_all_table_descriptions(
                        database_name=self._database_name, schema_name=schema_name
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
                                import json

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

            # ДОПОЛНИТЕЛЬНЫЙ ИСТОЧНИК: information_schema (для объектов без описаний)
            # Получаем список таблиц/представлений, которых нет в schema
            existing_tables = set(schema.keys())

            if schema_name is None:
                info_schema_query = """
                SELECT DISTINCT 
                    c.table_name,
                    c.table_schema,
                    CASE 
                        WHEN t.table_type = 'VIEW' THEN 'view'
                        ELSE 'table'
                    END as object_type
                FROM information_schema.columns c
                LEFT JOIN information_schema.tables t ON c.table_name = t.table_name AND c.table_schema = t.table_schema
                WHERE c.table_schema NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                ORDER BY c.table_schema, c.table_name
                """
                query_params = []
            else:
                info_schema_query = """
                SELECT DISTINCT 
                    c.table_name,
                    c.table_schema,
                    CASE 
                        WHEN t.table_type = 'VIEW' THEN 'view'
                        ELSE 'table'
                    END as object_type
                FROM information_schema.columns c
                LEFT JOIN information_schema.tables t ON c.table_name = t.table_name AND c.table_schema = t.table_schema
                WHERE c.table_schema = $1
                ORDER BY c.table_name
                """
                query_params = [schema_name]

            async with self.pool.acquire() as connection:
                info_result = await connection.fetch(info_schema_query, *query_params)

                # Добавляем таблицы/представления, которых нет в descriptions
                for row in info_result:
                    table_name = row["table_name"]
                    object_type = row["object_type"]
                    table_schema = row["table_schema"]

                    # Пропускаем если уже есть в schema или не нужны представления
                    if table_name in existing_tables:
                        continue
                    if not include_views and object_type == "view":
                        continue

                    # Получаем колонки для этой таблицы
                    columns_query = """
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns 
                    WHERE table_name = $1 AND table_schema = $2
                    ORDER BY ordinal_position
                    """

                    columns_result = await connection.fetch(columns_query, table_name, table_schema)

                    schema[table_name] = {
                        "columns": [],
                        "description": f"User data {object_type}",
                        "object_type": object_type,
                        "schema_name": table_schema,
                    }

                    for col_row in columns_result:
                        column_info = {
                            "name": col_row["column_name"],
                            "type": col_row["data_type"],
                            "datatype": col_row["data_type"],
                            "nullable": col_row["is_nullable"] == "YES",
                            "default": col_row["column_default"],
                        }
                        schema[table_name]["columns"].append(column_info)

            # Fallback на legacy описания из column_descriptions.json
            self._add_legacy_descriptions_to_fallback_objects(schema, existing_tables)

            tables_count = sum(1 for v in schema.values() if v.get("object_type") == "table")
            views_count = sum(1 for v in schema.values() if v.get("object_type") == "view")
            schema_info = "all schemas" if schema_name is None else f"{schema_name} schema"

            descriptions_count = len(existing_tables)
            fallback_count = len(schema) - descriptions_count

            logger.info(f"Retrieved schema from {schema_info}: {tables_count} tables, {views_count} views")
            logger.info(f"  - {descriptions_count} from database_descriptions")
            logger.info(f"  - {fallback_count} from information_schema fallback")

            return schema

        except Exception as e:
            logger.error(f"Failed to get data database schema: {str(e)}")
            raise Exception(f"Schema retrieval failed: {str(e)}")

    def _add_legacy_descriptions_to_fallback_objects(self, schema: Dict[str, Any], existing_tables: set):
        """Добавление legacy описаний только к объектам из information_schema"""
        try:
            if not DB_SCHEMA_CONTEXT:
                return

            # Применяем только к таблицам, которые НЕ были в database_descriptions
            for table_name in schema:
                if table_name in existing_tables:
                    continue  # Пропускаем объекты из database_descriptions

                for column_info in schema[table_name]["columns"]:
                    column_name = column_info["name"]

                    # Добавляем описание из column_descriptions.json если его нет
                    if "description" not in column_info and column_name in DB_SCHEMA_CONTEXT:
                        column_desc = DB_SCHEMA_CONTEXT[column_name]
                        if isinstance(column_desc, dict):
                            column_info["description"] = column_desc.get("описание", "")
                            column_info["datatype"] = column_desc.get("datatype", column_info["type"])
                            column_info["placeholder"] = column_desc.get("placeholder", "")
                            column_info["tags"] = column_desc.get("теги", "")

        except Exception as e:
            logger.warning(f"Failed to add legacy descriptions to fallback objects: {str(e)}")

    async def get_table_sample(self, table_name: str, limit: int = 5) -> DatabaseQueryResult:
        """Получение примера данных из таблицы"""
        try:
            # Простая проверка имени таблицы для безопасности
            if not table_name.replace("_", "").replace("-", "").isalnum():
                raise Exception("Invalid table name")

            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            return await self.execute_query(query)

        except Exception as e:
            logger.error(f"Failed to get table sample for {table_name}: {str(e)}")
            raise

    def get_schema_context(self) -> Dict[str, Any]:
        """Получение контекста схемы базы данных"""
        return DB_SCHEMA_CONTEXT or {}

    def get_database_name(self) -> str:
        """Получение имени текущей базы данных"""
        return self._database_name or "unknown"


# Создаем глобальный экземпляр сервиса
data_database_service = DataDatabaseService()
