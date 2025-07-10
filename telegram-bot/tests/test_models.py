"""
Тесты для моделей данных
"""

import pytest
from models import UserData, UserSettings, DatabaseTable, QueryResult, Language, ObjectType


class TestUserData:
    """Тесты для UserData"""

    def test_user_data_creation(self):
        """Тест создания UserData"""
        user_data = UserData(user_id="123456789", username="testuser", first_name="Test", last_name="User")

        assert user_data.user_id == "123456789"
        assert user_data.username == "testuser"
        assert user_data.first_name == "Test"
        assert user_data.last_name == "User"

    def test_user_data_with_none_values(self):
        """Тест создания UserData с None значениями"""
        user_data = UserData(user_id="123456789", username=None, first_name=None, last_name=None)

        assert user_data.user_id == "123456789"
        assert user_data.username is None
        assert user_data.first_name is None
        assert user_data.last_name is None


class TestUserSettings:
    """Тесты для UserSettings"""

    def test_default_settings(self):
        """Тест настроек по умолчанию"""
        settings = UserSettings()

        assert settings.preferred_language == Language.ENGLISH
        assert settings.show_explanation is True
        assert settings.show_sql is False

    def test_from_dict_english(self):
        """Тест создания из словаря (английский)"""
        data = {"preferred_language": "en", "show_explanation": True, "show_sql": False}

        settings = UserSettings.from_dict(data)

        assert settings.preferred_language == Language.ENGLISH
        assert settings.show_explanation is True
        assert settings.show_sql is False

    def test_from_dict_russian(self):
        """Тест создания из словаря (русский)"""
        data = {"preferred_language": "ru", "show_explanation": False, "show_sql": True}

        settings = UserSettings.from_dict(data)

        assert settings.preferred_language == Language.RUSSIAN
        assert settings.show_explanation is False
        assert settings.show_sql is True

    def test_from_dict_missing_values(self):
        """Тест создания из словаря с отсутствующими значениями"""
        data = {}

        settings = UserSettings.from_dict(data)

        assert settings.preferred_language == Language.ENGLISH
        assert settings.show_explanation is True
        assert settings.show_sql is False


class TestDatabaseTable:
    """Тесты для DatabaseTable"""

    def test_table_creation(self):
        """Тест создания таблицы"""
        table = DatabaseTable(
            full_name="public.users",
            schema_name="public",
            table_name="users",
            object_type=ObjectType.TABLE,
            description="User accounts table",
        )

        assert table.full_name == "public.users"
        assert table.schema_name == "public"
        assert table.table_name == "users"
        assert table.object_type == ObjectType.TABLE
        assert table.description == "User accounts table"

    def test_view_creation(self):
        """Тест создания представления"""
        view = DatabaseTable(
            full_name="analytics.sales_view",
            schema_name="analytics",
            table_name="sales_view",
            object_type=ObjectType.VIEW,
        )

        assert view.full_name == "analytics.sales_view"
        assert view.object_type == ObjectType.VIEW
        assert view.description is None

    def test_from_dict(self):
        """Тест создания из словаря"""
        data = {
            "full_name": "public.products",
            "schema_name": "public",
            "table_name": "products",
            "object_type": "table",
            "description": "Products catalog",
        }

        table = DatabaseTable.from_dict(data)

        assert table.full_name == "public.products"
        assert table.schema_name == "public"
        assert table.table_name == "products"
        assert table.object_type == ObjectType.TABLE
        assert table.description == "Products catalog"


class TestQueryResult:
    """Тесты для QueryResult"""

    def test_successful_result(self):
        """Тест успешного результата"""
        data = [{"id": 1, "name": "Product 1"}, {"id": 2, "name": "Product 2"}]

        result = QueryResult(
            success=True,
            message="Query executed successfully",
            data=data,
            sql_query="SELECT * FROM products LIMIT 2",
            explanation="Retrieved first 2 products",
            execution_time=0.15,
            row_count=2,
        )

        assert result.success is True
        assert result.message == "Query executed successfully"
        assert len(result.data) == 2
        assert result.data[0]["name"] == "Product 1"
        assert result.sql_query == "SELECT * FROM products LIMIT 2"
        assert result.explanation == "Retrieved first 2 products"
        assert result.execution_time == 0.15
        assert result.row_count == 2

    def test_failed_result(self):
        """Тест неудачного результата"""
        result = QueryResult(success=False, message="Table not found", data=[])

        assert result.success is False
        assert result.message == "Table not found"
        assert len(result.data) == 0
        assert result.sql_query is None
        assert result.execution_time is None
        assert result.row_count == 0

    def test_from_dict(self):
        """Тест создания из словаря"""
        data = {
            "success": True,
            "message": "Success",
            "data": [{"id": 1, "value": "test"}],
            "sql_query": "SELECT * FROM test",
            "explanation": "Test query",
            "execution_time": 0.1,
            "row_count": 1,
        }

        result = QueryResult.from_dict(data)

        assert result.success is True
        assert result.message == "Success"
        assert len(result.data) == 1
        assert result.sql_query == "SELECT * FROM test"
        assert result.explanation == "Test query"
        assert result.execution_time == 0.1
        assert result.row_count == 1

    def test_from_dict_minimal(self):
        """Тест создания из минимального словаря"""
        data = {"success": False, "message": "Error"}

        result = QueryResult.from_dict(data)

        assert result.success is False
        assert result.message == "Error"
        assert result.data == []
        assert result.sql_query is None
        assert result.execution_time is None
        assert result.row_count == 0


class TestEnums:
    """Тесты для перечислений"""

    def test_language_enum(self):
        """Тест перечисления языков"""
        assert Language.ENGLISH.value == "en"
        assert Language.RUSSIAN.value == "ru"

    def test_object_type_enum(self):
        """Тест перечисления типов объектов"""
        assert ObjectType.TABLE.value == "table"
        assert ObjectType.VIEW.value == "view"
