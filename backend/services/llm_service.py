import openai
from langchain_openai import ChatOpenAI
import time
import re
import logging
from typing import Optional, Dict, Any

from config.settings import settings, DB_SCHEMA_CONTEXT
from models.schemas import LLMQueryRequest, LLMQueryResponse

from loguru import logger


class LLMService:
    """Сервис для работы с LLM (OpenAI)"""

    def __init__(self):
        """Инициализация LLM сервиса"""
        self.llm = ChatOpenAI(
            model_name=settings.openai_model,
            temperature=settings.openai_temperature,
            openai_api_key=settings.openai_api_key,
        )

        logger.info(f"LLM Service initialized with model: {settings.openai_model}")

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
            # Создаем промпт для генерации SQL
            prompt = self._create_sql_prompt(natural_query)

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
                sql_query=sql_query,
                explanation=self._clean_markdown(response.content),
                execution_time=execution_time,
                model_used=settings.openai_model,
            )

            logger.info(f"SQL query generated successfully in {execution_time:.2f}s")

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"LLM query generation failed after {execution_time:.2f}s: {str(e)}")
            raise Exception(f"Ошибка генерации SQL запроса: {str(e)}")

    def _create_sql_prompt(self, natural_query: str) -> str:
        """Создает промпт для генерации SQL запроса"""
        prompt = f"""
Ты - эксперт по SQL запросам. На основе описания схемы базы данных и пользовательского запроса на естественном языке, сгенерируй корректный SQL запрос.

ИМЯ ТАБЛИЦЫ: demo1.bills_view
ОПИСАНИЕ ТАБЛИЦЫ: таблица чеков. Представление, содержащее все чеки из базы данных.

ОПИСАНИЕ ПОЛЕЙ ТАБЛИЦЫ:
{DB_SCHEMA_CONTEXT}

ЗАПРОС ПОЛЬЗОВАТЕЛЯ: {natural_query}

ИНСТРУКЦИИ:
1. Сгенерируй только SQL запрос SELECT (никаких UPDATE, DELETE, INSERT, DROP)
2. Используй именя колонок из описания колонок таблицы.
3. Используй только таблицы и колонки из предоставленной схемы
4. Запрос должен быть валидным PostgreSQL
5. Если запрос невозможно выполнить с данной схемой, объясни почему
5. Не используй подзапросы без необходимости
6. Используй корректные типы данных

ОТВЕТ ДОЛЖЕН СОДЕРЖАТЬ:
- SQL запрос в блоке ```sql
- Краткое объяснение запроса

ПРИМЕР ОТВЕТА:
```sql
SELECT name, email FROM users WHERE created_at > '2023-01-01';
```
Этот запрос выбирает имена и email всех пользователей, созданных после 1 января 2023 года.
"""
        return prompt

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
            "status": "active",
        }


# Создаем глобальный экземпляр сервиса
llm_service = LLMService()
