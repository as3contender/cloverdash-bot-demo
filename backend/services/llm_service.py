import openai
from langchain_openai import ChatOpenAI
import time
import re
import logging
from typing import Optional, Dict, Any

from config.settings import settings
from services.data_database import data_database_service
from models.llm import LLMQueryResponse

logger = logging.getLogger(__name__)


class LLMService:
    """Сервис для работы с LLM (OpenAI)"""

    def __init__(self):
        """Инициализация LLM сервиса"""
        try:
            self.llm = ChatOpenAI(
                model_name=settings.openai_model,
                temperature=settings.openai_temperature,
                openai_api_key=settings.openai_api_key,
            )
            # Проверяем, что API ключ настроен
            self.is_configured = bool(settings.openai_api_key and settings.openai_api_key.strip())

            logger.info(f"LLM Service initialized with model: {settings.openai_model}")
            logger.info(f"LLM Service configured: {self.is_configured}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM Service: {e}")
            self.is_configured = False
            self.llm = None

    async def generate_sql_query(self, natural_query: str) -> LLMQueryResponse:
        """
        Генерирует SQL запрос на основе естественного языка

        Args:
            natural_query: Запрос на естественном языке

        Returns:
            LLMQueryResponse: Ответ с сгенерированным SQL запросом
        """
        start_time = time.time()

        try:
            # Проверяем, что LLM сервис настроен
            if not self.is_configured or not self.llm:
                raise Exception("LLM сервис не настроен или недоступен")

            # Создаем промпт для генерации SQL
            prompt = await self._create_sql_prompt(natural_query)

            # Отправляем запрос к OpenAI
            response = self.llm.invoke(prompt)
            logger.debug(f"Response: {response}")

            # Извлекаем SQL из ответа
            sql_query = self._extract_sql_from_response(response.content)
            logger.debug(f"SQL query: {sql_query}")

            # Валидируем SQL на предмет безопасности
            if not self._validate_sql_security(sql_query):
                raise Exception("SQL запрос не прошел проверку безопасности")

            execution_time = time.time() - start_time

            result = LLMQueryResponse(
                sql_query=sql_query, explanation=self._clean_markdown(response.content), execution_time=execution_time
            )

            logger.info(f"SQL query generated successfully in {execution_time:.2f}s")

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"LLM query generation failed after {execution_time:.2f}s: {str(e)}")
            raise Exception(f"Ошибка генерации SQL запроса: {str(e)}")

    async def _create_sql_prompt(self, natural_query: str) -> str:
        """Создает промпт для генерации SQL запроса"""

        # Получаем актуальную схему базы данных
        try:
            db_schema = await self._get_database_schema()
            schema_description = self._format_schema_for_prompt(db_schema)
        except Exception as e:
            logger.warning(f"Failed to get database schema: {e}")
            schema_description = "Схема базы данных недоступна. Используйте стандартные имена таблиц."

        prompt = f"""
Ты - эксперт по SQL запросам. На основе описания схемы базы данных и пользовательского запроса на естественном языке, сгенерируй корректный SQL запрос.

СХЕМА БАЗЫ ДАННЫХ:
{schema_description}

ЗАПРОС ПОЛЬЗОВАТЕЛЯ: {natural_query}

ИНСТРУКЦИИ:
1. Сгенерируй только SQL запрос SELECT (никаких UPDATE, DELETE, INSERT, DROP)
2. Используй имена колонок из описания схемы базы данных.
3. Используй только таблицы и колонки из предоставленной схемы
4. Запрос должен быть валидным PostgreSQL
5. Если запрос невозможно выполнить с данной схемой, объясни почему
6. Не используй подзапросы без необходимости
7. Используй корректные типы данных
8. Добавляй разумные ограничения (LIMIT) для больших результатов

ОТВЕТ ДОЛЖЕН СОДЕРЖАТЬ:
- SQL запрос в блоке ```sql
- Краткое объяснение запроса

ПРИМЕР ОТВЕТА:
```sql
SELECT name, email FROM users WHERE created_at > '2023-01-01' LIMIT 100;
```
Этот запрос выбирает имена и email всех пользователей, созданных после 1 января 2023 года, с ограничением до 100 записей.

Ответ выводи на английском языке.
"""
        return prompt

    async def _get_database_schema(self) -> Dict[str, Any]:
        """Получение схемы базы данных пользовательских данных"""
        try:
            # Импортируем здесь, чтобы избежать циклических импортов
            from services.app_database import app_database_service
            from services.data_database import data_database_service

            if app_database_service.is_connected and data_database_service.is_connected:
                # Получаем имя базы данных
                database_name = data_database_service.get_database_name()
                # Получаем схему со всеми представлениями и схемами из app_database
                return await app_database_service.get_database_schema(
                    database_name=database_name, include_views=True, schema_name=None
                )
            else:
                logger.warning("Databases not connected - no schema available")
                return {}
        except Exception as e:
            logger.warning(f"Failed to get database schema: {e}")
            return {}

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

            schema_text += "КОЛОНКИ:\n"
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
        # Ищем SQL блок в markdown
        sql_pattern = r"```sql\s*(.*?)\s*```"
        match = re.search(sql_pattern, response, re.DOTALL | re.IGNORECASE)

        if match:
            return match.group(1).strip()

        # Если не найден markdown блок, ищем строки, начинающиеся с SELECT
        lines = response.split("\n")
        for line in lines:
            line = line.strip()
            if line.upper().startswith("SELECT"):
                return line

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
            "INFORMATION_SCHEMA",
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
