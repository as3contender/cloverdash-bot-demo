import openai
from langchain_openai import ChatOpenAI
import time
import re
import logging
from typing import Optional, Dict, Any
import httpx

from config.settings import settings
from services.data_database import data_database_service
from services.app_database import app_database_service
from models.llm import LLMQueryResponse

logger = logging.getLogger(__name__)


class LLMService:
    """Сервис для работы с LLM (OpenAI)"""

    def __init__(self):
        """Инициализация LLM сервиса"""
        try:
            # Настройка HTTP клиента с прокси если указан
            http_client = None
            if settings.openai_proxy:
                logger.info(f"Using proxy: {settings.openai_proxy}")
                http_client = httpx.Client(proxies=settings.openai_proxy)
            
            # Настройка базового URL если указан
            base_url = settings.openai_base_url
            
            self.llm = ChatOpenAI(
                model_name=settings.openai_model,
                temperature=settings.openai_temperature,
                openai_api_key=settings.openai_api_key,
                base_url=base_url,
                http_client=http_client,
            )
            # Проверяем, что API ключ настроен
            self.is_configured = bool(settings.openai_api_key and settings.openai_api_key.strip())

            logger.info(f"LLM Service initialized with model: {settings.openai_model}")
            logger.info(f"LLM Service configured: {self.is_configured}")
            if base_url:
                logger.info(f"Using custom base URL: {base_url}")
            if settings.openai_proxy:
                logger.info(f"Using proxy: {settings.openai_proxy}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM Service: {e}")
            self.is_configured = False
            self.llm = None

    async def generate_sql_query_with_user_permissions(
        self, 
        natural_query: str, 
        user_id: str, 
        user_language: str = "ru"
    ) -> LLMQueryResponse:
        """
        Генерирует SQL запрос на основе естественного языка с учетом прав пользователя
        
        Args:
            natural_query: Запрос на естественном языке
            user_id: ID пользователя для проверки прав
            user_language: Язык пользователя для ответа ('en' или 'ru')
            
        Returns:
            LLMQueryResponse: Ответ с сгенерированным SQL запросом
        """
        if not self.is_configured or not self.llm:
            raise Exception("LLM Admin не настроен или недоступен")
        
        try:
            # Создаем промпт с учетом прав пользователя
            prompt = await self._create_sql_prompt_with_user_permissions(
                natural_query, user_id, user_language
            )
            
            # Отправляем запрос к LLM
            response = await self.llm.ainvoke(prompt)
            
            # Извлекаем SQL из ответа
            sql_query = self._extract_sql_from_response(response.content)
            
            # Валидируем SQL на предмет безопасности
            if not self._validate_sql_security(sql_query):
                raise Exception("SQL запрос не прошел проверку безопасности")
            
            result = LLMQueryResponse(
                sql_query=sql_query,
                explanation=self._clean_markdown(response.content),
                execution_time=0.0  # Будет заполнено позже
            )
            
            logger.info(f"SQL query generated successfully for user {user_id}")
            logger.info(f"Generated SQL query: {sql_query}")
            
            # Дополнительная диагностика безопасности
            try:
                from services.data_database import data_database_service
                data_database_service._validate_sql_security(sql_query)
                logger.info("✅ Generated SQL passed security validation")
            except Exception as security_error:
                logger.error(f"❌ Generated SQL failed security validation: {str(security_error)}")
                logger.info(f"🔍 SQL that failed: {sql_query}")
            
            return result
            
        except Exception as e:
            logger.error(f"LLM query generation failed for user {user_id}: {str(e)}")
            raise Exception(f"Ошибка генерации SQL запроса: {str(e)}")

    async def _create_sql_prompt_with_user_permissions(
        self, 
        natural_query: str, 
        user_id: str, 
        user_language: str = "en"
    ) -> str:
        """Создает LLM промпт с учетом прав пользователя"""
        
        # Получаем схему БД с правами пользователя
        schema = await self._get_database_schema_with_user_permissions(user_id)
        schema_description = self._format_schema_for_prompt(schema)
        logger.info(f"User ID: {user_id}, Schema description: {schema_description}")
        prompt = f"""
Ты - эксперт по SQL запросам. На основе описания схемы базы данных и пользовательского запроса на естественном языке, сгенерируй корректный SQL запрос.

{schema_description}

ЗАПРОС ПОЛЬЗОВАТЕЛЯ: {natural_query}

ВАЖНЫЕ ПРАВИЛА:
- Генерируй только SELECT запросы
- Используй только таблицы, доступные пользователю {user_id}
- НЕ указывай префикс схемы в FROM (используй просто имя таблицы, например: FROM users)
- ИСКЛЮЧЕНИЕ: Для системных функций (CURRENT_DATE, CURRENT_TIME, NOW(), etc.) НЕ используй FROM
- Отвечай на языке: {user_language}
- Объясни логику запроса

СПЕЦИАЛЬНЫЕ ИНСТРУКЦИИ ДЛЯ ТАБЛИЦЫ users:
- Для подсчета пользователей используй: SELECT COUNT(*) FROM users
- Для получения списка пользователей используй: SELECT * FROM users
- Для фильтрации по имени используй колонку: full_name
- Для фильтрации по Telegram ID используй колонку: telegram_id
- Для фильтрации по статусу используй колонку: is_active

ПРИМЕР ПРАВИЛЬНОГО SQL ЗАПРОСА:
```sql
SELECT COUNT(*) AS total_users 
FROM users 
WHERE is_active = true
```

SQL запрос:
```sql
"""
        
        return prompt

    def _get_language_instruction(self, user_language: str) -> str:
        """Возвращает инструкцию по языку ответа в зависимости от настроек пользователя"""
        if user_language == "ru":
            return "Ответ выводи на русском языке."
        else:
            return "Provide response in English."

    async def _get_user_database_from_mapping(self, user_id: str) -> str:
        """Получает базу данных пользователя из маппинга"""
        try:
            query = """
            SELECT database_name 
            FROM users_role_bd_mapping 
            WHERE user_id::VARCHAR = $1
            LIMIT 1
            """
            
            result = await app_database_service.execute_query(query, [user_id])
            
            if result.data:
                database_name = result.data[0]['database_name']
                logger.info(f"User {user_id} mapped to database: {database_name}")
                return database_name
            else:
                logger.warning(f"User {user_id} not found in mapping")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user database from mapping: {str(e)}")
            return None

    async def _get_user_schema_from_mapping(self, user_id: str) -> str:
        """Получает схему пользователя из маппинга"""
        try:
            query = """
            SELECT schema_name 
            FROM users_role_bd_mapping 
            WHERE user_id::VARCHAR = $1
            LIMIT 1
            """
            
            result = await app_database_service.execute_query(query, [user_id])
            
            if result.data:
                schema_name = result.data[0]['schema_name']
                logger.info(f"User {user_id} mapped to schema: {schema_name}")
                return schema_name
            else:
                logger.warning(f"User {user_id} not found in mapping")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user schema from mapping: {str(e)}")
            return None

    async def _get_database_schema_with_user_permissions(self, user_id: str) -> Dict[str, Any]:
        """Получает схему БД с учетом прав пользователя"""
        
        try:
            # Получаем базу данных пользователя из маппинга
            database_name = await self._get_user_database_from_mapping(user_id)
            
            if not database_name:
                logger.warning(f"User {user_id} not found in mapping, using default database")
                database_name = data_database_service.get_database_name()
            
            # Получаем схему с правами пользователя
            # Сначала получаем схему пользователя из маппинга
            schema_name = await self._get_user_schema_from_mapping(user_id)
            if not schema_name:
                schema_name = "public"  # Fallback к public
                
            schema = await app_database_service.get_database_schema_with_user_permissions(
                user_id=user_id,
                database_name=database_name,
                include_views=True,
                schema_name=schema_name
            )
            
            logger.info(f"Database schema retrieved for user {user_id}: {len(schema)} tables")
            return schema
            
        except Exception as e:
            logger.error(f"Failed to get database schema for user {user_id}: {e}")
            # Возвращаем базовую схему в случае ошибки
            return {
                "users": {
                    "description": "Таблица пользователей (базовая)",
                    "columns": [
                        {"name": "id", "description": "ID пользователя", "datatype": "uuid"},
                        {"name": "username", "description": "Имя пользователя", "datatype": "varchar"}
                    ]
                }
            }

    def _format_schema_for_prompt(self, db_schema: Dict[str, Any]) -> str:
        """Форматирует схему базы данных для промпта"""
        if not db_schema:
            return "Схема базы данных недоступна."

        schema_text = "ДОСТУПНЫЕ ОБЪЕКТЫ БАЗЫ ДАННЫХ:\n\n"

        for table_name, table_info in db_schema.items():
            object_type = table_info.get("object_type", "table")
            schema_name = table_info.get("schema_name", "public")

            # Показываем тип объекта (таблица или представление)
            object_label = "ПРЕДСТАВЛЕНИЕ" if object_type == "view" else "ТАБЛИЦА"
            full_name = f"{schema_name}.{table_name}" if schema_name != "public" else table_name

            schema_text += f"{object_label}: {full_name}\n"
            if "description" in table_info:
                schema_text += f"ОПИСАНИЕ: {table_info['description']}\n"

            # Специальное форматирование для bills таблицы
            if table_name == "bills":
                schema_text += "ВАЖНО: Это основная таблица для анализа продаж!\n"
                schema_text += "КЛЮЧЕВЫЕ КОЛОНКИ ДЛЯ АНАЛИЗА:\n"
                schema_text += "  - bill_key: ключ чека\n"
                schema_text += "  - bill_date: дата чека\n"
                schema_text += "  - bill_time: время чека\n"
                schema_text += "  - bill_code: код чека\n"
                schema_text += "  - customer_id: идентификатор покупателя\n"
                schema_text += "  - goods_type: тип товара\n"
                schema_text += "  - goods_group: группа товара\n"
                schema_text += "  - goods_name: название товара\n"
                schema_text += "  - goods_full_name: полное название товара\n"
                schema_text += "  - row_quantity: количество товара\n"
                schema_text += "  - row_amount: цена товара\n"
                schema_text += "  - row_sum: сумма товара\n"
                schema_text += "  - row_sale: скидка на товар\n"
                schema_text += "  - customer_name: имя клиента\n"

            schema_text += "ВСЕ КОЛОНКИ:\n"
            for column in table_info.get("columns", []):
                col_name = column.get("name", "")
                # Используем datatype из описаний, если доступен, иначе базовый type
                col_type = column.get("datatype", column.get("type", ""))
                col_desc = column.get("description", "")
                nullable = " (может быть NULL)" if column.get("nullable") else ""

                schema_text += f"  - {col_name} ({col_type}){nullable}"
                if col_desc:
                    schema_text += f" - {col_desc}"
                schema_text += "\n"
            schema_text += "\n"

        return schema_text

    def _extract_sql_from_response(self, response: str) -> str:
        """Извлекает SQL запрос из ответа LLM"""
        logger.info(f"🔍 LLM Response: {response}")  # Логируем полный ответ
        
        # Ищем SQL блок в markdown
        sql_pattern = r"```sql\s*(.*?)\s*```"
        match = re.search(sql_pattern, response, re.DOTALL | re.IGNORECASE)

        if match:
            sql_query = match.group(1).strip()
            logger.info(f"📋 Extracted SQL from markdown: {sql_query}")
            return sql_query

        # Если не найден markdown блок, ищем многострочный SQL запрос
        lines = response.split("\n")
        sql_lines = []
        in_sql = False
        
        for line in lines:
            line = line.strip()
            if line.upper().startswith("SELECT"):
                in_sql = True
                sql_lines.append(line)
            elif in_sql and (line.upper().startswith(("FROM", "WHERE", "GROUP BY", "HAVING", "ORDER BY", "LIMIT")) or 
                           line.startswith(("FROM", "WHERE", "GROUP BY", "HAVING", "ORDER BY", "LIMIT")) or
                           line.endswith(";")):
                sql_lines.append(line)
                if line.endswith(";"):
                    break
            elif in_sql and line == "":
                sql_lines.append(line)
            elif in_sql and not line.upper().startswith(("SELECT", "FROM", "WHERE", "GROUP BY", "HAVING", "ORDER BY", "LIMIT")):
                # Если встретили не-SQL строку, заканчиваем
                break

        if sql_lines:
            extracted_sql = "\n".join(sql_lines).strip()
            logger.info(f"📋 Extracted SQL from plain text: {extracted_sql}")
            return extracted_sql

        raise Exception("SQL запрос не найден в ответе LLM")

    def _validate_sql_security(self, sql_query: str) -> bool:
        """Проверяет SQL запрос на безопасность"""
        sql_upper = sql_query.upper().strip()

        # Разрешаем только SELECT запросы
        if not sql_upper.startswith("SELECT"):
            return False

        # Запрещенные команды и функции (как отдельные слова)
        forbidden_keywords = [
            "DROP",
            "DELETE",
            "UPDATE",
            "INSERT",
            "ALTER",
            "TRUNCATE",
            "CREATE",
            "GRANT",
            "REVOKE",
            "EXEC",
            "EXECUTE",
            "PROCEDURE",
            "FUNCTION",
            "TRIGGER",
            # "INFORMATION_SCHEMA",  # Разрешаем запросы к information_schema для безопасных операций
        ]

        # Специальные символы (как подстроки)
        forbidden_symbols = ["--", "/*", "*/"]

        # Запрещенные префиксы
        forbidden_prefixes = ["SP_", "PG_", "POSTGRES", "ADMIN"]

        # Разбиваем SQL на слова для проверки
        words = re.findall(r"\b\w+\b", sql_upper)

        # Проверяем запрещенные ключевые слова как отдельные слова
        for word in words:
            if word in forbidden_keywords:
                return False

            # Проверяем префиксы
            for prefix in forbidden_prefixes:
                if word.startswith(prefix):
                    return False

        # Проверяем запрещенные символы как подстроки
        for symbol in forbidden_symbols:
            if symbol in sql_upper:
                return False

        return True

    def _clean_markdown(self, text: str) -> str:
        """Очищает markdown разметку из текста"""
        # Удаляем SQL блоки
        text = re.sub(r"```sql.*?```", "", text, flags=re.DOTALL | re.IGNORECASE)

        # Удаляем другие блоки кода
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)

        # Удаляем markdown форматирование
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # **bold**
        text = re.sub(r"\*(.*?)\*", r"\1", text)  # *italic*
        text = re.sub(r"`(.*?)`", r"\1", text)  # `code`

        # Очищаем лишние пробелы и переносы
        text = re.sub(r"\n\s*\n", "\n\n", text)
        text = text.strip()

        return text

    async def test_connection(self) -> bool:
        """
        Тестирует подключение к LLM сервису

        Returns:
            bool: True если подключение успешно, False в противном случае
        """
        try:
            # Проверяем, что сервис настроен
            if not self.is_configured or not self.llm:
                logger.warning("LLM service not configured")
                return False

            test_prompt = "Напиши простой SQL запрос для выбора всех записей из таблицы test"
            response = self.llm.invoke(test_prompt)
            return bool(response and response.content)

        except Exception as e:
            logger.error(f"LLM connection test failed: {str(e)}")
            return False

    def get_service_info(self) -> Dict[str, Any]:
        """
        Возвращает информацию о LLM сервисе

        Returns:
            Dict: Информация о сервисе
        """
        return {
            "service": "LLM Service",
            "model": settings.openai_model,
            "temperature": settings.openai_temperature,
            "configured": self.is_configured,
            "status": "active" if self.is_configured else "not configured",
        }


# Создаем глобальный экземпляр сервиса
llm_service = LLMService()
