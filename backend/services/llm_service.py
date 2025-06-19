import openai
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from typing import Optional
import logging
import time

from config.settings import settings, DB_SCHEMA_CONTEXT

logger = logging.getLogger(__name__)


class LLMService:
    """Сервис для работы с LLM (OpenAI)"""

    def __init__(self):
        """Инициализация сервиса LLM"""
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model
        self.temperature = settings.openai_temperature

        # Настройка OpenAI
        openai.api_key = self.api_key

        # Инициализация LangChain модели
        self.llm = ChatOpenAI(temperature=self.temperature, model=self.model, openai_api_key=self.api_key)

        logger.info(f"LLM Service initialized with model: {self.model}")

    def generate_sql_query(self, question: str, user_id: Optional[str] = None) -> tuple[str, float]:
        """
        Генерирует SQL запрос на основе вопроса пользователя

        Args:
            question: Вопрос пользователя на естественном языке
            user_id: ID пользователя (для логирования)

        Returns:
            tuple: (SQL запрос, время выполнения)
        """
        start_time = time.time()

        try:
            # Создаем системный промпт
            system_prompt = self._create_system_prompt()

            # Создаем промпт пользователя
            human_prompt = f"Вопрос пользователя: {question}"

            # Логируем запрос
            logger.info(f"Generating SQL for user {user_id}: {question}")

            # Получаем ответ от LLM
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)]

            response = self.llm(messages)
            sql_query = response.content.strip()

            # Очищаем SQL от возможных markdown блоков
            sql_query = self._clean_sql_query(sql_query)

            execution_time = time.time() - start_time

            logger.info(f"SQL generated in {execution_time:.2f}s: {sql_query}")

            return sql_query, execution_time

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error generating SQL query: {str(e)}")
            raise Exception(f"Ошибка генерации SQL запроса: {str(e)}")

    def _create_system_prompt(self) -> str:
        """Создает системный промпт для LLM"""
        return f"""
Ты - эксперт по SQL запросам. Твоя задача - создать безопасный SQL запрос на основе вопроса пользователя.

Контекст базы данных:
{DB_SCHEMA_CONTEXT}

ВАЖНЫЕ ПРАВИЛА:
1. Возвращай ТОЛЬКО SQL запрос, без дополнительного текста и объяснений
2. Используй ТОЛЬКО SELECT запросы - никаких INSERT, UPDATE, DELETE, DROP и других модифицирующих операций
3. Запрос должен быть безопасным и не содержать потенциально вредоносного кода
4. Используй стандартный SQL синтаксис (PostgreSQL)
5. Если вопрос неясен или невозможно создать запрос, верни: "-- Невозможно создать запрос для данного вопроса"
6. Не используй подзапросы без необходимости
7. Ограничивай результаты разумным количеством строк (используй LIMIT)
8. Используй правильные JOIN'ы для связанных таблиц

Примеры хороших запросов:
- SELECT COUNT(*) FROM orders WHERE created_at >= NOW() - INTERVAL '1 month';
- SELECT name, email FROM users ORDER BY created_at DESC LIMIT 10;
- SELECT AVG(amount) as average_order FROM orders;
"""

    def _clean_sql_query(self, sql_query: str) -> str:
        """Очищает SQL запрос от markdown и лишних символов"""
        # Удаляем markdown блоки
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        if sql_query.startswith("```"):
            sql_query = sql_query[3:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]

        # Удаляем лишние пробелы и переносы строк
        sql_query = sql_query.strip()

        return sql_query

    def validate_sql_query(self, sql_query: str) -> bool:
        """
        Валидирует SQL запрос на безопасность

        Args:
            sql_query: SQL запрос для валидации

        Returns:
            bool: True если запрос безопасен, False в противном случае
        """
        # Преобразуем в нижний регистр для проверки
        query_lower = sql_query.lower().strip()

        # Запрещенные операции
        forbidden_keywords = [
            "insert",
            "update",
            "delete",
            "drop",
            "create",
            "alter",
            "truncate",
            "exec",
            "execute",
            "sp_",
            "xp_",
            "--",
            ";--",
            "union",
            "information_schema",
            "pg_",
        ]

        # Проверяем наличие запрещенных ключевых слов
        for keyword in forbidden_keywords:
            if keyword in query_lower:
                logger.warning(f"Forbidden keyword detected: {keyword}")
                return False

        # Проверяем, что запрос начинается с SELECT
        if not query_lower.startswith("select"):
            logger.warning("Query does not start with SELECT")
            return False

        return True


# Создаем глобальный экземпляр сервиса
llm_service = LLMService()
