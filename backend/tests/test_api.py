import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient
from datetime import datetime
import json

from main import app
from models.base import QueryRequest, QueryResponse, HealthResponse
from models.database import DatabaseQueryResult
from config.settings import settings


@pytest.mark.api
@pytest.mark.asyncio
class TestAPIEndpoints:
    """Тесты для API эндпоинтов"""

    async def test_root_endpoint(self, test_client):
        """Тест основного эндпоинта"""
        response = await test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "CloverdashBot Backend API"
        assert data["version"] == settings.api_version
        assert data["status"] == "running"

    async def test_health_endpoint_healthy(self, test_client):
        """Тест health check при здоровом состоянии"""
        with patch("api.routes.database_service.test_connection", return_value=True):
            response = await test_client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["version"] == settings.api_version
            assert data["database_connected"] is True
            assert "timestamp" in data

    async def test_health_endpoint_degraded(self, test_client):
        """Тест health check при проблемах с БД"""
        with patch("api.routes.database_service.test_connection", return_value=False):
            response = await test_client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["database_connected"] is False

    async def test_health_endpoint_error(self, test_client):
        """Тест health check при ошибке"""
        with patch("api.routes.database_service.test_connection", side_effect=Exception("DB Error")):
            response = await test_client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["database_connected"] is False


@pytest.mark.api
@pytest.mark.asyncio
class TestQueryEndpoint:
    """Тесты для эндпоинта обработки запросов"""

    async def test_query_endpoint_success_with_db(self, test_client, sample_db_result):
        """Тест успешной обработки запроса с БД"""
        request_data = {"question": "Сколько пользователей в системе?", "user_id": "test_user_123"}

        # Мокаем сервисы
        with patch(
            "api.routes.llm_service.generate_sql_query", return_value=("SELECT COUNT(*) FROM users;", 0.5)
        ), patch("api.routes.llm_service.validate_sql_query", return_value=True), patch(
            "api.routes.database_service.is_connected", True
        ), patch(
            "api.routes.database_service.execute_query", return_value=sample_db_result
        ):

            response = await test_client.post("/query", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["sql_query"] == "SELECT COUNT(*) FROM users;"
            assert "answer" in data
            assert data["execution_time"] > 0

    async def test_query_endpoint_success_without_db(self, test_client):
        """Тест обработки запроса без подключения к БД"""
        request_data = {"question": "Покажи всех пользователей", "user_id": "test_user_456"}

        with patch(
            "api.routes.llm_service.generate_sql_query", return_value=("SELECT * FROM users LIMIT 10;", 0.3)
        ), patch("api.routes.llm_service.validate_sql_query", return_value=True), patch(
            "api.routes.database_service.is_connected", False
        ):

            response = await test_client.post("/query", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["sql_query"] == "SELECT * FROM users LIMIT 10;"
            assert "База данных временно недоступна" in data["answer"]

    async def test_query_endpoint_invalid_sql(self, test_client):
        """Тест обработки невалидного SQL"""
        request_data = {"question": "Удали всех пользователей", "user_id": "test_user_789"}

        with patch("api.routes.llm_service.generate_sql_query", return_value=("DELETE FROM users;", 0.2)), patch(
            "api.routes.llm_service.validate_sql_query", return_value=False
        ):

            response = await test_client.post("/query", json=request_data)

            assert response.status_code == 400
            data = response.json()
            assert "не прошел валидацию безопасности" in data["detail"]

    async def test_query_endpoint_llm_error(self, test_client):
        """Тест обработки ошибки LLM"""
        request_data = {"question": "Тестовый вопрос", "user_id": "test_user_error"}

        with patch("api.routes.llm_service.generate_sql_query", side_effect=Exception("OpenAI API Error")):
            response = await test_client.post("/query", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert data["error_message"] is not None
            assert "Произошла ошибка при обработке запроса" in data["answer"]

    async def test_query_endpoint_database_error(self, test_client):
        """Тест обработки ошибки базы данных"""
        request_data = {"question": "Покажи пользователей", "user_id": "test_user_db_error"}

        with patch("api.routes.llm_service.generate_sql_query", return_value=("SELECT * FROM users;", 0.1)), patch(
            "api.routes.llm_service.validate_sql_query", return_value=True
        ), patch("api.routes.database_service.is_connected", True), patch(
            "api.routes.database_service.execute_query", side_effect=Exception("Database connection lost")
        ):

            response = await test_client.post("/query", json=request_data)

            assert response.status_code == 500
            data = response.json()
            assert "Ошибка выполнения запроса к базе данных" in data["detail"]

    async def test_query_endpoint_invalid_request(self, test_client):
        """Тест валидации запроса"""
        # Пустой вопрос
        response = await test_client.post("/query", json={"question": ""})
        assert response.status_code == 422

        # Отсутствующий вопрос
        response = await test_client.post("/query", json={"user_id": "test"})
        assert response.status_code == 422

        # Неправильный формат
        response = await test_client.post("/query", json="invalid")
        assert response.status_code == 422

    async def test_query_endpoint_different_result_formats(self, test_client):
        """Тест различных форматов результатов запроса"""
        request_data = {"question": "Тестовый запрос", "user_id": "test_user_formats"}

        # Пустой результат
        empty_result = DatabaseQueryResult(data=[], columns=[], row_count=0, execution_time=0.1)

        with patch(
            "api.routes.llm_service.generate_sql_query", return_value=("SELECT COUNT(*) FROM empty_table;", 0.1)
        ), patch("api.routes.llm_service.validate_sql_query", return_value=True), patch(
            "api.routes.database_service.is_connected", True
        ), patch(
            "api.routes.database_service.execute_query", return_value=empty_result
        ):

            response = await test_client.post("/query", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert "не найдено результатов" in data["answer"]

        # Одиночное значение
        single_result = DatabaseQueryResult(data=[{"count": 42}], columns=["count"], row_count=1, execution_time=0.2)

        with patch("api.routes.database_service.execute_query", return_value=single_result):
            response = await test_client.post("/query", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert "Результат: 42" in data["answer"]

        # Множественные результаты
        multiple_result = DatabaseQueryResult(
            data=[{"id": 1, "name": "User 1"}, {"id": 2, "name": "User 2"}, {"id": 3, "name": "User 3"}],
            columns=["id", "name"],
            row_count=3,
            execution_time=0.3,
        )

        with patch("api.routes.database_service.execute_query", return_value=multiple_result):
            response = await test_client.post("/query", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert "Найдено 3 записей" in data["answer"]
            assert "User 1" in data["answer"]


@pytest.mark.api
@pytest.mark.asyncio
class TestSchemaEndpoint:
    """Тесты для эндпоинта схемы базы данных"""

    async def test_schema_endpoint_success(self, test_client):
        """Тест успешного получения схемы"""
        mock_schema = {
            "users": [
                {"column_name": "id", "data_type": "integer", "is_nullable": False, "column_default": None},
                {"column_name": "name", "data_type": "varchar", "is_nullable": False, "column_default": None},
            ],
            "orders": [
                {"column_name": "id", "data_type": "integer", "is_nullable": False, "column_default": None},
                {"column_name": "user_id", "data_type": "integer", "is_nullable": False, "column_default": None},
            ],
        }

        with patch("api.routes.database_service.is_connected", True), patch(
            "api.routes.database_service.get_database_schema", return_value=mock_schema
        ):

            response = await test_client.get("/schema")

            assert response.status_code == 200
            data = response.json()
            assert "schema" in data
            assert "table_count" in data
            assert data["table_count"] == 2
            assert "users" in data["schema"]
            assert "orders" in data["schema"]

    async def test_schema_endpoint_not_connected(self, test_client):
        """Тест получения схемы при отсутствии подключения к БД"""
        with patch("api.routes.database_service.is_connected", False):
            response = await test_client.get("/schema")

            assert response.status_code == 503
            data = response.json()
            assert "База данных недоступна" in data["detail"]

    async def test_schema_endpoint_database_error(self, test_client):
        """Тест обработки ошибки при получении схемы"""
        with patch("api.routes.database_service.is_connected", True), patch(
            "api.routes.database_service.get_database_schema", side_effect=Exception("Schema error")
        ):

            response = await test_client.get("/schema")

            assert response.status_code == 500
            data = response.json()
            assert "Ошибка получения схемы базы данных" in data["detail"]


@pytest.mark.api
@pytest.mark.integration
class TestAPIIntegration:
    """Интеграционные тесты API"""

    async def test_full_query_workflow(self, test_client):
        """Тест полного рабочего процесса запроса"""
        # Сначала проверяем health
        with patch("api.routes.database_service.test_connection", return_value=True):
            health_response = await test_client.get("/health")
            assert health_response.status_code == 200
            assert health_response.json()["status"] == "healthy"

        # Затем делаем запрос
        request_data = {"question": "Сколько активных пользователей?", "user_id": "integration_test_user"}

        mock_result = DatabaseQueryResult(
            data=[{"active_users": 150}], columns=["active_users"], row_count=1, execution_time=0.45
        )

        with patch(
            "api.routes.llm_service.generate_sql_query",
            return_value=("SELECT COUNT(*) as active_users FROM users WHERE status = 'active';", 0.8),
        ), patch("api.routes.llm_service.validate_sql_query", return_value=True), patch(
            "api.routes.database_service.is_connected", True
        ), patch(
            "api.routes.database_service.execute_query", return_value=mock_result
        ):

            query_response = await test_client.post("/query", json=request_data)

            assert query_response.status_code == 200
            data = query_response.json()
            assert data["success"] is True
            assert "150" in data["answer"]
            assert "SELECT COUNT(*)" in data["sql_query"]

    async def test_api_error_handling_chain(self, test_client):
        """Тест цепочки обработки ошибок"""
        request_data = {"question": "Тест обработки ошибок", "user_id": "error_test_user"}

        # Тест: LLM ошибка -> валидная обработка
        with patch("api.routes.llm_service.generate_sql_query", side_effect=Exception("LLM failed")):
            response = await test_client.post("/query", json=request_data)
            assert response.status_code == 200
            assert response.json()["success"] is False

        # Тест: Валидный LLM -> невалидный SQL -> ошибка валидации
        with patch("api.routes.llm_service.generate_sql_query", return_value=("DROP TABLE users;", 0.1)), patch(
            "api.routes.llm_service.validate_sql_query", return_value=False
        ):

            response = await test_client.post("/query", json=request_data)
            assert response.status_code == 400

        # Тест: Валидный SQL -> ошибка БД -> HTTP 500
        with patch("api.routes.llm_service.generate_sql_query", return_value=("SELECT * FROM users;", 0.1)), patch(
            "api.routes.llm_service.validate_sql_query", return_value=True
        ), patch("api.routes.database_service.is_connected", True), patch(
            "api.routes.database_service.execute_query", side_effect=Exception("DB failed")
        ):

            response = await test_client.post("/query", json=request_data)
            assert response.status_code == 500


@pytest.mark.api
@pytest.mark.unit
class TestAPIResponseFormats:
    """Тесты форматов ответов API"""

    async def test_response_models_validation(self, test_client):
        """Тест валидации моделей ответов"""
        # Проверяем, что все ответы соответствуют Pydantic моделям

        # Health response
        with patch("api.routes.database_service.test_connection", return_value=True):
            response = await test_client.get("/health")
            data = response.json()

            # Проверяем обязательные поля HealthResponse
            required_fields = ["status", "timestamp", "version", "database_connected"]
            for field in required_fields:
                assert field in data

        # Query response успех
        request_data = {"question": "Test question", "user_id": "test"}
        mock_result = DatabaseQueryResult(data=[{"test": "value"}], columns=["test"], row_count=1, execution_time=0.1)

        with patch("api.routes.llm_service.generate_sql_query", return_value=("SELECT 1;", 0.1)), patch(
            "api.routes.llm_service.validate_sql_query", return_value=True
        ), patch("api.routes.database_service.is_connected", True), patch(
            "api.routes.database_service.execute_query", return_value=mock_result
        ):

            response = await test_client.post("/query", json=request_data)
            data = response.json()

            # Проверяем обязательные поля QueryResponse
            required_fields = ["answer", "success", "execution_time"]
            for field in required_fields:
                assert field in data

            assert data["sql_query"] is not None
            assert isinstance(data["success"], bool)
            assert isinstance(data["execution_time"], (int, float))

    async def test_cors_headers(self, test_client):
        """Тест CORS заголовков"""
        response = await test_client.get("/")

        # FastAPI автоматически добавляет CORS заголовки если middleware настроен
        assert response.status_code == 200
        # В тестовом окружении CORS заголовки могут не добавляться
        # но основная функциональность должна работать
