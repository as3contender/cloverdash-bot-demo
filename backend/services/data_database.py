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
        Только SELECT запросы для безопасности с дополнительными проверками
        """
        if not self.is_connected or not self.pool:
            raise Exception("Data database is not connected")

        # Строгая проверка безопасности SQL запроса
        self._validate_sql_security(query)

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

    async def execute_query_with_user(self, query: str, user_id: str) -> DatabaseQueryResult:
        """
        Выполнение SQL запроса от имени конкретного пользователя с использованием его роли
        
        Args:
            query: SQL запрос для выполнения
            user_id: ID пользователя, от имени которого выполняется запрос
            
        Returns:
            DatabaseQueryResult: Результат выполнения запроса
        """
        if not self.is_connected or not self.pool:
            raise Exception("Data database is not connected")

        # Строгая проверка безопасности SQL запроса
        self._validate_sql_security(query)

        start_time = datetime.now()

        try:
            # Получаем роль пользователя из базы данных приложения
            user_role = await self._get_user_role(user_id)
            
            if not user_role:
                raise Exception(f"User {user_id} not found or has no assigned role")

            logger.info(f"Executing query for user {user_id} with role {user_role}")

            # Создаем новое подключение от имени роли пользователя
            async with self.pool.acquire() as connection:
                # Логируем детали подключения
                current_user = await connection.fetchval("SELECT current_user")
                current_db = await connection.fetchval("SELECT current_database()")
                logger.info(f"🔍 Before SET ROLE - current_user: {current_user}, database: {current_db}")
                
                # Устанавливаем роль для текущей сессии
                await connection.execute(f"SET ROLE {user_role}")
                
                # Устанавливаем search_path для роли на основе схемы пользователя
                user_schema = await self._get_user_schema(user_id)
                if user_schema and user_schema != "public":
                    await connection.execute(f"SET search_path TO {user_schema}, public")
                    logger.info(f"🔍 Set search_path to {user_schema}, public for {user_role}")
                else:
                    # Для ролей без специальной схемы используем только public
                    await connection.execute("SET search_path TO public")
                    logger.info(f"🔍 Set search_path to public for {user_role}")
                
                # Проверяем роль после установки
                current_user_after = await connection.fetchval("SELECT current_user")
                search_path_after = await connection.fetchval("SHOW search_path")
                logger.info(f"🔍 After SET ROLE - current_user: {current_user_after}, search_path: {search_path_after}")
                
                # Логируем запрос
                logger.info(f"🔍 Executing query: {query}")
                
                # Выполняем запрос
                result = await connection.fetch(query)

                # Преобразуем результат в список словарей
                data = []
                columns = []

                if result:
                    columns = list(result[0].keys())
                    for row in result:
                        data.append(dict(row))

                execution_time = (datetime.now() - start_time).total_seconds()

                logger.info(f"Data query executed successfully for user {user_id}: {len(data)} rows in {execution_time:.2f}s")

                return DatabaseQueryResult(
                    data=data, columns=columns, row_count=len(data), execution_time=execution_time
                )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Data database query failed for user {user_id}: {str(e)}")
            raise Exception(f"Query execution failed: {str(e)}")

    async def _get_user_role(self, user_id: str) -> str:
        """
        Получает роль пользователя из базы данных приложения
        
        Args:
            user_id: ID пользователя
            
        Returns:
            str: Роль пользователя или None если не найдена
        """
        try:
            from services.app_database import app_database_service
            
            if not app_database_service.is_connected:
                raise Exception("Application database is not connected")

            # Получаем роль пользователя из таблицы users_role_bd_mapping
            # Используем CAST для преобразования user_id в VARCHAR, так как в таблице может быть UUID
            query = """
            SELECT role_name 
            FROM users_role_bd_mapping 
            WHERE user_id::VARCHAR = $1
            LIMIT 1
            """
            
            result = await app_database_service.execute_query(query, [user_id])
            
            if result.data:
                role_name = result.data[0]['role_name']
                logger.info(f"Found role '{role_name}' for user {user_id}")
                return role_name
            else:
                logger.warning(f"No role found for user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get role for user {user_id}: {str(e)}")
            raise Exception(f"Failed to get user role: {str(e)}")

    async def _get_user_schema(self, user_id: str) -> str:
        """
        Получает схему пользователя из базы данных приложения
        
        Args:
            user_id: ID пользователя
            
        Returns:
            str: Схема пользователя или None если не найдена
        """
        try:
            from services.app_database import app_database_service
            
            if not app_database_service.is_connected:
                raise Exception("Application database is not connected")

            # Получаем схему пользователя из таблицы users_role_bd_mapping
            query = """
            SELECT schema_name 
            FROM users_role_bd_mapping 
            WHERE user_id::VARCHAR = $1
            LIMIT 1
            """
            
            result = await app_database_service.execute_query(query, [user_id])
            
            if result.data:
                schema_name = result.data[0]['schema_name']
                logger.info(f"Found schema '{schema_name}' for user {user_id}")
                return schema_name
            else:
                logger.warning(f"No schema found for user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get schema for user {user_id}: {str(e)}")
            raise Exception(f"Failed to get user schema: {str(e)}")

    def _validate_sql_security(self, query: str) -> None:
        """Строгая валидация SQL запроса на безопасность"""
        if not query or not query.strip():
            raise Exception("Empty query not allowed")

        # Удаляем комментарии и нормализуем
        cleaned_query = self._clean_sql_query(query)

        # Проверяем, что это SELECT запрос
        if not cleaned_query.upper().strip().startswith("SELECT"):
            raise Exception("Only SELECT queries are allowed")

        # Список запрещенных ключевых слов (DDL/DML команды)
        dangerous_keywords = [
            "DROP",
            "DELETE",
            "INSERT",
            "UPDATE",
            "CREATE",
            "ALTER",
            "TRUNCATE",
            "GRANT",
            "REVOKE",
            "MERGE",
            "REPLACE",
            "CALL",
            "EXEC",
            "EXECUTE",
            "DECLARE",
            "CURSOR",
            "PROCEDURE",
            "FUNCTION",
            "TRIGGER",
            "VIEW",
            "INDEX",
            "DATABASE",
            "SCHEMA",
            "TABLE",
            "COLUMN",
            "CONSTRAINT",
        ]

        # Проверяем наличие опасных команд
        for keyword in dangerous_keywords:
            # Используем word boundaries для точного поиска
            import re

            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, cleaned_query, re.IGNORECASE):
                logger.info(f"🔍 Found dangerous keyword: '{keyword}' in query: {cleaned_query}")
                # Исключение: разрешаем TABLE в information_schema.tables для безопасных запросов
                if keyword == "TABLE" and "information_schema.tables" in cleaned_query:
                    logger.info(f"✅ Allowing TABLE keyword in information_schema.tables context")
                    continue
                logger.error(f"❌ Blocking dangerous keyword: '{keyword}'")
                raise Exception(f"Dangerous keyword '{keyword}' not allowed in queries")

        # Проверяем на подозрительные функции
        dangerous_functions = [
            "pg_sleep",
            "pg_terminate_backend",
            "pg_cancel_backend",
            "pg_reload_conf",
            "pg_rotate_logfile",
            "pg_read_file",
            "pg_write_file",
            "copy",
            "\\copy",
            "lo_import",
            "lo_export",
        ]

        for func in dangerous_functions:
            if func.lower() in cleaned_query.lower():
                raise Exception(f"Dangerous function '{func}' not allowed")

        # Проверяем длину запроса
        if len(query) > 5000:
            raise Exception("Query too long (max 5000 characters)")

        # Проверяем на множественные команды (;)
        # Разрешаем только один SELECT запрос
        statements = [s.strip() for s in cleaned_query.split(";") if s.strip()]
        if len(statements) > 1:
            raise Exception("Multiple statements not allowed")

        logger.info("SQL query passed security validation")

    def _clean_sql_query(self, query: str) -> str:
        """Очистка SQL запроса от комментариев"""
        import re

        # Удаляем однострочные комментарии --
        query = re.sub(r"--.*$", "", query, flags=re.MULTILINE)

        # Удаляем многострочные комментарии /* */
        query = re.sub(r"/\*.*?\*/", "", query, flags=re.DOTALL)

        # Удаляем лишние пробелы и переводы строк
        query = " ".join(query.split())

        return query

    async def get_table_sample(self, table_name: str, limit: int = 5) -> DatabaseQueryResult:
        """Получение примера данных из таблицы"""
        try:
            # Проверка имени таблицы для безопасности - разрешаем schema.table формат
            import re

            # Разрешаем только буквы, цифры, подчеркивания, дефисы и точки (для схем)
            if not re.match(r"^[a-zA-Z0-9_.-]+$", table_name):
                raise Exception("Invalid table name format")

            # Защита от SQL injection - проверяем, что нет подозрительных символов
            if any(
                char in table_name for char in [";", "--", "/*", "*/", "union", "drop", "delete", "insert", "update"]
            ):
                raise Exception("Invalid table name - contains restricted characters")

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
