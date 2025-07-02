import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import asyncpg

from services.data_database import data_database_service
from models.database import DatabaseQueryResult


@pytest.mark.database
@pytest.mark.unit
class TestDatabaseService:
    """Тесты для сервиса базы данных"""

    def test_database_service_initialization(self):
        """Тест инициализации сервиса базы данных"""
        service = DatabaseService()
        assert service.database_url is not None
        assert service.pool is None
        assert service._connection_status is False

    @pytest.mark.asyncio
    async def test_initialize_connection_pool_success(self, mock_db_pool):
        """Тест успешной инициализации пула соединений"""
        service = DatabaseService()

        with patch("services.database.asyncpg.create_pool", return_value=mock_db_pool):
            await service.initialize()

            assert service.pool is not None
            assert service.is_connected is True

    @pytest.mark.asyncio
    async def test_initialize_connection_pool_failure(self):
        """Тест неудачной инициализации пула соединений"""
        service = DatabaseService()

        with patch("services.database.asyncpg.create_pool", side_effect=Exception("Connection failed")):
            with pytest.raises(Exception, match="Connection failed"):
                await service.initialize()

            assert service.pool is None
            assert service.is_connected is False

    @pytest.mark.asyncio
    async def test_close_connection_pool(self, database_service_mock):
        """Тест закрытия пула соединений"""
        service = database_service_mock

        await service.close()

        service.pool.close.assert_called_once()
        assert service._connection_status is False

    @pytest.mark.asyncio
    async def test_execute_query_success(self, database_service_mock, mock_db_connection):
        """Тест успешного выполнения запроса"""
        service = database_service_mock
        sql_query = "SELECT * FROM users LIMIT 2;"

        # Настраиваем мок для возврата данных
        mock_rows = [
            {"id": 1, "name": "Test User", "email": "test@example.com"},
            {"id": 2, "name": "Another User", "email": "another@example.com"},
        ]
        mock_db_connection.fetch.return_value = [MagicMock(**row, keys=lambda: row.keys()) for row in mock_rows]

        result = await service.execute_query(sql_query)

        assert isinstance(result, DatabaseQueryResult)
        assert result.row_count == 2
        assert result.columns == ["id", "name", "email"]
        assert len(result.data) == 2
        assert result.execution_time > 0

        mock_db_connection.fetch.assert_called_once_with(sql_query)

    @pytest.mark.asyncio
    async def test_execute_query_empty_result(self, database_service_mock, mock_db_connection):
        """Тест выполнения запроса с пустым результатом"""
        service = database_service_mock
        sql_query = "SELECT * FROM users WHERE id = 999;"

        mock_db_connection.fetch.return_value = []

        result = await service.execute_query(sql_query)

        assert isinstance(result, DatabaseQueryResult)
        assert result.row_count == 0
        assert result.columns == []
        assert result.data == []
        assert result.execution_time > 0

    @pytest.mark.asyncio
    async def test_execute_query_database_error(self, database_service_mock, mock_db_connection):
        """Тест обработки ошибки базы данных"""
        service = database_service_mock
        sql_query = "SELECT * FROM non_existent_table;"

        mock_db_connection.fetch.side_effect = asyncpg.PostgresError("Table does not exist")

        with pytest.raises(Exception, match="Ошибка выполнения запроса к базе данных"):
            await service.execute_query(sql_query)

    @pytest.mark.asyncio
    async def test_execute_query_not_connected(self):
        """Тест выполнения запроса при отсутствии соединения"""
        service = DatabaseService()
        sql_query = "SELECT * FROM users;"

        with pytest.raises(Exception, match="База данных недоступна"):
            await service.execute_query(sql_query)

    @pytest.mark.asyncio
    async def test_test_connection_success(self, database_service_mock, mock_db_connection):
        """Тест успешной проверки соединения"""
        service = database_service_mock
        mock_db_connection.fetchval.return_value = 1

        result = await service.test_connection()

        assert result is True
        mock_db_connection.fetchval.assert_called_once_with("SELECT 1")

    @pytest.mark.asyncio
    async def test_test_connection_failure(self, database_service_mock, mock_db_connection):
        """Тест неудачной проверки соединения"""
        service = database_service_mock
        mock_db_connection.fetchval.side_effect = Exception("Connection lost")

        result = await service.test_connection()

        assert result is False

    @pytest.mark.asyncio
    async def test_test_connection_no_pool(self):
        """Тест проверки соединения без пула"""
        service = DatabaseService()

        result = await service.test_connection()

        assert result is False

    @pytest.mark.asyncio
    async def test_get_database_schema_success(self, database_service_mock, mock_db_connection):
        """Тест получения схемы базы данных"""
        service = database_service_mock

        # Настраиваем мок для возврата схемы
        schema_rows = [
            {
                "table_name": "users",
                "column_name": "id",
                "data_type": "integer",
                "is_nullable": "NO",
                "column_default": "nextval('users_id_seq'::regclass)",
            },
            {
                "table_name": "users",
                "column_name": "name",
                "data_type": "character varying",
                "is_nullable": "NO",
                "column_default": None,
            },
            {
                "table_name": "orders",
                "column_name": "id",
                "data_type": "integer",
                "is_nullable": "NO",
                "column_default": "nextval('orders_id_seq'::regclass)",
            },
            {
                "table_name": "orders",
                "column_name": "user_id",
                "data_type": "integer",
                "is_nullable": "NO",
                "column_default": None,
            },
        ]

        mock_db_connection.fetch.return_value = [MagicMock(**row) for row in schema_rows]

        schema = await service.get_database_schema()

        assert "users" in schema
        assert "orders" in schema
        assert len(schema["users"]) == 2
        assert len(schema["orders"]) == 2
        assert schema["users"][0]["column_name"] == "id"
        assert schema["users"][1]["column_name"] == "name"

    @pytest.mark.asyncio
    async def test_get_database_schema_not_connected(self):
        """Тест получения схемы при отсутствии соединения"""
        service = DatabaseService()

        with pytest.raises(Exception, match="База данных недоступна"):
            await service.get_database_schema()

    @pytest.mark.asyncio
    async def test_get_connection_context_manager(self, database_service_mock, mock_db_connection):
        """Тест контекстного менеджера для соединения"""
        service = database_service_mock

        async with service.get_connection() as connection:
            assert connection == mock_db_connection

    @pytest.mark.asyncio
    async def test_get_connection_context_manager_not_connected(self):
        """Тест контекстного менеджера без соединения"""
        service = DatabaseService()

        with pytest.raises(Exception, match="База данных недоступна"):
            async with service.get_connection():
                pass

    def test_is_connected_property(self):
        """Тест свойства is_connected"""
        service = DatabaseService()

        # Изначально не подключен
        assert service.is_connected is False

        # Эмулируем подключение
        service.pool = MagicMock()
        service._connection_status = True
        assert service.is_connected is True

        # Эмулируем отключение
        service.pool = None
        assert service.is_connected is False


@pytest.mark.database
@pytest.mark.integration
class TestDatabaseIntegration:
    """Интеграционные тесты для базы данных"""

    @pytest.mark.asyncio
    async def test_database_service_lifecycle(self, mock_db_pool):
        """Тест полного жизненного цикла сервиса базы данных"""
        service = DatabaseService()

        # Инициализация
        with patch("services.database.asyncpg.create_pool", return_value=mock_db_pool):
            await service.initialize()
            assert service.is_connected is True

        # Тестирование соединения
        with patch.object(service.pool, "acquire") as mock_acquire:
            mock_connection = AsyncMock()
            mock_connection.fetchval.return_value = 1
            mock_acquire.return_value.__aenter__.return_value = mock_connection
            mock_acquire.return_value.__aexit__.return_value = None

            connection_test = await service.test_connection()
            assert connection_test is True

        # Закрытие
        await service.close()
        assert service.is_connected is False
