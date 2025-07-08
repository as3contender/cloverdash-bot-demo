import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
import os
import sys

# Добавляем родительский каталог в путь для импорта модулей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app
from config.settings import Settings
from services.data_database import DataDatabaseService
from services.llm_service import llm_service
from models.database import DatabaseQueryResult


@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для всей сессии тестирования"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings():
    """Тестовые настройки"""
    return Settings(
        openai_api_key="test_api_key",
        openai_model="gpt-3.5-turbo",
        database_url="postgresql://test:test@localhost:5432/test_db",
        api_host="127.0.0.1",
        api_port=8001,
        log_level="DEBUG",
    )


@pytest.fixture
def mock_db_connection():
    """Мок соединения с базой данных"""
    mock_connection = AsyncMock()
    mock_connection.fetch.return_value = [
        {"id": 1, "name": "Test User", "email": "test@example.com"},
        {"id": 2, "name": "Another User", "email": "another@example.com"},
    ]
    mock_connection.fetchval.return_value = 1
    return mock_connection


@pytest.fixture
def mock_db_pool(mock_db_connection):
    """Мок пула соединений с базой данных"""
    mock_pool = AsyncMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_db_connection
    mock_pool.acquire.return_value.__aexit__.return_value = None
    return mock_pool


@pytest.fixture
def database_service_mock(mock_db_pool):
    """Мок сервиса базы данных"""
    with patch("services.data_database.asyncpg.create_pool", return_value=mock_db_pool):
        service = DataDatabaseService()
        service.pool = mock_db_pool
        service.is_connected = True
        yield service


@pytest.fixture
def sample_db_result():
    """Пример результата запроса к БД"""
    return DatabaseQueryResult(
        data=[
            {"id": 1, "name": "Test User", "email": "test@example.com"},
            {"id": 2, "name": "Another User", "email": "another@example.com"},
        ],
        columns=["id", "name", "email"],
        row_count=2,
        execution_time=0.123,
    )


@pytest.fixture
def mock_openai_response():
    """Мок ответа от OpenAI"""
    mock_response = MagicMock()
    mock_response.content = "SELECT COUNT(*) FROM users;"
    return mock_response


@pytest.fixture
def llm_service_mock(mock_openai_response):
    """Мок сервиса LLM"""
    with patch("services.llm_service.ChatOpenAI") as mock_llm_class:
        mock_llm = MagicMock()
        mock_llm.return_value = mock_openai_response
        mock_llm_class.return_value = mock_llm

        # Мокаем LLMService
        with patch.object(llm_service, "llm", mock_llm):
            llm_service.is_connected = True
            yield llm_service


@pytest.fixture
async def test_client():
    """HTTP клиент для тестирования API"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def column_descriptions():
    """Пример описания колонок базы данных"""
    return {
        "users": {
            "id": {"type": "integer", "description": "Уникальный идентификатор пользователя"},
            "name": {"type": "varchar", "description": "Имя пользователя"},
            "email": {"type": "varchar", "description": "Email пользователя"},
            "created_at": {"type": "timestamp", "description": "Дата создания"},
        },
        "orders": {
            "id": {"type": "integer", "description": "Уникальный идентификатор заказа"},
            "user_id": {"type": "integer", "description": "ID пользователя"},
            "amount": {"type": "decimal", "description": "Сумма заказа"},
            "status": {"type": "varchar", "description": "Статус заказа"},
            "created_at": {"type": "timestamp", "description": "Дата создания заказа"},
        },
    }


@pytest.fixture
def temp_column_descriptions_file(column_descriptions, tmp_path):
    """Временный файл с описанием колонок для тестов"""
    file_path = tmp_path / "column_descriptions.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(column_descriptions, f, ensure_ascii=False, indent=2)

    # Мокаем путь к файлу в настройках
    original_open = open

    def mock_open(filename, *args, **kwargs):
        if "column_descriptions.json" in filename:
            return original_open(file_path, *args, **kwargs)
        return original_open(filename, *args, **kwargs)

    with patch("builtins.open", side_effect=mock_open):
        yield file_path


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Автоматическая настройка тестового окружения"""
    # Мокаем настройки для избежания валидационных ошибок
    with patch("config.settings.settings") as mock_settings:
        mock_settings.openai_api_key = "test_key"
        mock_settings.openai_model = "gpt-3.5-turbo"
        mock_settings.openai_temperature = 0
        mock_settings.get_database_url.return_value = "postgresql://test:test@localhost:5432/test_db"
        mock_settings.api_version = "1.0.0"
        mock_settings.log_level = "DEBUG"
        yield
