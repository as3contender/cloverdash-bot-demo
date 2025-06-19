import pytest
from unittest.mock import patch, MagicMock
import time

from services.llm_service import LLMService, llm_service
from langchain.schema import HumanMessage, SystemMessage


@pytest.mark.llm
@pytest.mark.unit
class TestLLMService:
    """Тесты для сервиса LLM"""

    def test_llm_service_initialization(self):
        """Тест инициализации сервиса LLM"""
        with patch("services.llm_service.ChatOpenAI") as mock_llm:
            with patch("services.llm_service.openai"):
                service = LLMService()
                assert service.api_key is not None
                assert service.model == "gpt-3.5-turbo"
                assert service.temperature == 0
                assert service.llm is not None

    @pytest.mark.asyncio
    async def test_generate_sql_query_success(self, llm_service_mock):
        """Тест успешной генерации SQL запроса"""
        service = llm_service_mock
        question = "Сколько пользователей в системе?"
        user_id = "test_user_123"

        # Настраиваем мок для возврата SQL
        mock_response = MagicMock()
        mock_response.content = "SELECT COUNT(*) FROM users;"
        service.llm.return_value = mock_response

        sql_query, execution_time = service.generate_sql_query(question, user_id)

        assert sql_query == "SELECT COUNT(*) FROM users;"
        assert execution_time > 0
        assert isinstance(execution_time, float)

        # Проверяем, что LLM был вызван с правильными аргументами
        service.llm.assert_called_once()
        call_args = service.llm.call_args[0][0]
        assert len(call_args) == 2
        assert isinstance(call_args[0], SystemMessage)
        assert isinstance(call_args[1], HumanMessage)
        assert question in call_args[1].content

    @pytest.mark.asyncio
    async def test_generate_sql_query_with_markdown(self, llm_service_mock):
        """Тест генерации SQL запроса с markdown форматированием"""
        service = llm_service_mock
        question = "Покажи всех пользователей"

        # SQL с markdown блоками
        mock_response = MagicMock()
        mock_response.content = "```sql\nSELECT * FROM users LIMIT 10;\n```"
        service.llm.return_value = mock_response

        sql_query, execution_time = service.generate_sql_query(question)

        # Проверяем, что markdown был удален
        assert sql_query == "SELECT * FROM users LIMIT 10;"
        assert "```" not in sql_query

    @pytest.mark.asyncio
    async def test_generate_sql_query_llm_error(self, llm_service_mock):
        """Тест обработки ошибки LLM"""
        service = llm_service_mock
        question = "Неправильный вопрос"

        service.llm.side_effect = Exception("OpenAI API error")

        with pytest.raises(Exception, match="Ошибка генерации SQL запроса"):
            await service.generate_sql_query(question)

    def test_create_system_prompt(self, llm_service_mock):
        """Тест создания системного промпта"""
        service = llm_service_mock
        prompt = service._create_system_prompt()

        assert "эксперт по SQL запросам" in prompt
        assert "SELECT" in prompt
        assert "PostgreSQL" in prompt
        assert "безопасным" in prompt

    def test_clean_sql_query_with_markdown(self, llm_service_mock):
        """Тест очистки SQL запроса от markdown"""
        service = llm_service_mock

        # Тест с различными вариантами markdown
        test_cases = [
            ("```sql\nSELECT * FROM users;\n```", "SELECT * FROM users;"),
            ("```\nSELECT * FROM users;\n```", "SELECT * FROM users;"),
            ("SELECT * FROM users;", "SELECT * FROM users;"),
            ("  \n  SELECT * FROM users;  \n  ", "SELECT * FROM users;"),
        ]

        for input_sql, expected_output in test_cases:
            result = service._clean_sql_query(input_sql)
            assert result == expected_output

    def test_validate_sql_query_valid_queries(self, llm_service_mock):
        """Тест валидации корректных SQL запросов"""
        service = llm_service_mock

        valid_queries = [
            "SELECT * FROM users;",
            "SELECT COUNT(*) FROM orders WHERE status = 'active';",
            "SELECT u.name, o.amount FROM users u JOIN orders o ON u.id = o.user_id;",
            "select name from users order by created_at desc limit 10;",
        ]

        for query in valid_queries:
            assert service.validate_sql_query(query) is True

    def test_validate_sql_query_invalid_queries(self, llm_service_mock):
        """Тест валидации некорректных SQL запросов"""
        service = llm_service_mock

        invalid_queries = [
            "INSERT INTO users (name) VALUES ('test');",
            "UPDATE users SET name = 'new_name' WHERE id = 1;",
            "DELETE FROM users WHERE id = 1;",
            "DROP TABLE users;",
            "CREATE TABLE test_table (id int);",
            "ALTER TABLE users ADD COLUMN test varchar(50);",
            "TRUNCATE TABLE users;",
            "SELECT * FROM users UNION SELECT * FROM orders;",
            "SELECT * FROM information_schema.tables;",
            "EXEC sp_helpdb;",
            "UPDATE users SET name = 'test'; SELECT * FROM users;",
            "-- comment",
            "SELECT * FROM pg_database;",
        ]

        for query in invalid_queries:
            assert service.validate_sql_query(query) is False

    def test_validate_sql_query_non_select(self, llm_service_mock):
        """Тест валидации запросов, не начинающихся с SELECT"""
        service = llm_service_mock

        non_select_queries = [
            "EXPLAIN SELECT * FROM users;",
            "WITH cte AS (SELECT * FROM users) SELECT * FROM cte;",
            "",
        ]

        for query in non_select_queries:
            assert service.validate_sql_query(query) is False

    @pytest.mark.asyncio
    async def test_generate_sql_query_performance(self, llm_service_mock):
        """Тест производительности генерации SQL запроса"""
        service = llm_service_mock
        question = "Тестовый вопрос"

        mock_response = MagicMock()
        mock_response.content = "SELECT 1;"
        service.llm.return_value = mock_response

        start_time = time.time()
        sql_query, execution_time = service.generate_sql_query(question)
        actual_time = time.time() - start_time

        # Проверяем, что время выполнения измеряется корректно
        assert execution_time <= actual_time + 0.1  # Небольшая погрешность
        assert execution_time > 0

    def test_validate_sql_query_case_insensitive(self, llm_service_mock):
        """Тест регистронезависимой валидации SQL запросов"""
        service = llm_service_mock

        # Тестируем разные регистры
        queries = [
            ("SELECT * FROM users;", True),
            ("select * from users;", True),
            ("SeLeCt * FrOm UsErS;", True),
            ("INSERT INTO users VALUES (1);", False),
            ("insert into users values (1);", False),
            ("InSeRt InTo UsErS vAlUeS (1);", False),
        ]

        for query, expected in queries:
            assert service.validate_sql_query(query) == expected


@pytest.mark.llm
@pytest.mark.integration
class TestLLMIntegration:
    """Интеграционные тесты для LLM сервиса"""

    @pytest.mark.asyncio
    async def test_llm_service_full_workflow(self, llm_service_mock):
        """Тест полного рабочего процесса LLM сервиса"""
        service = llm_service_mock
        question = "Найди топ-5 пользователей по количеству заказов"
        user_id = "integration_test_user"

        # Настраиваем мок для возврата сложного SQL
        mock_response = MagicMock()
        mock_response.content = """```sql
        SELECT u.name, COUNT(o.id) as order_count
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        GROUP BY u.id, u.name
        ORDER BY order_count DESC
        LIMIT 5;
        ```"""
        service.llm.return_value = mock_response

        # Генерируем SQL
        sql_query, execution_time = service.generate_sql_query(question, user_id)

        # Проверяем корректность очистки
        assert "```" not in sql_query
        assert "SELECT u.name, COUNT(o.id)" in sql_query
        assert "LIMIT 5" in sql_query

        # Проверяем валидацию
        is_valid = service.validate_sql_query(sql_query)
        assert is_valid is True

        # Проверяем, что время выполнения записано
        assert execution_time > 0


@pytest.mark.llm
@pytest.mark.unit
class TestLLMServiceEdgeCases:
    """Тесты граничных случаев для LLM сервиса"""

    def test_validate_empty_query(self, llm_service_mock):
        """Тест валидации пустого запроса"""
        service = llm_service_mock
        assert service.validate_sql_query("") is False
        assert service.validate_sql_query("   ") is False
        assert service.validate_sql_query("\n\t") is False

    def test_clean_sql_query_edge_cases(self, llm_service_mock):
        """Тест очистки SQL в граничных случаях"""
        service = llm_service_mock

        edge_cases = [
            ("", ""),
            ("   ", ""),
            ("\n\t\r", ""),
            ("```", ""),
            ("```sql```", ""),
            ("```sql\n```", ""),
            ("```\nSELECT 1;\n```\nSome extra text", "SELECT 1;\n```\nSome extra text"),
        ]

        for input_sql, expected_output in edge_cases:
            result = service._clean_sql_query(input_sql)
            assert result == expected_output

    @pytest.mark.asyncio
    async def test_generate_sql_query_with_special_characters(self, llm_service_mock):
        """Тест генерации SQL с специальными символами"""
        service = llm_service_mock
        question = "Найди пользователей с именем содержащим 'O'Connor'"

        mock_response = MagicMock()
        mock_response.content = "SELECT * FROM users WHERE name LIKE '%O''Connor%';"
        service.llm.return_value = mock_response

        sql_query, _ = service.generate_sql_query(question)

        assert "O''Connor" in sql_query
        assert service.validate_sql_query(sql_query) is True
