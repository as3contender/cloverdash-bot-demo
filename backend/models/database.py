"""
Схемы для работы с базой данных
"""

from pydantic import BaseModel, Field
from typing import List, Any, Dict


class SchemaResponse(BaseModel):
    """Ответ со схемой базы данных"""

    success: bool = Field(..., description="Статус получения схемы")
    message: str = Field(..., description="Сообщение о результате")
    database_schema: Dict[str, Any] = Field(..., description="Схема базы данных")
    table_count: int = Field(..., description="Количество таблиц")


class DatabaseQueryResult(BaseModel):
    """Результат выполнения SQL запроса"""

    data: List[Dict[str, Any]] = Field(..., description="Данные результата")
    columns: List[str] = Field(..., description="Названия колонок")
    row_count: int = Field(..., description="Количество строк")
    execution_time: float = Field(..., description="Время выполнения запроса")

    model_config = {
        "json_schema_extra": {
            "example": {
                "data": [
                    {"id": 1, "name": "John", "email": "john@example.com"},
                    {"id": 2, "name": "Jane", "email": "jane@example.com"},
                ],
                "columns": ["id", "name", "email"],
                "row_count": 2,
                "execution_time": 0.045,
            }
        }
    }


class TableDescriptionRequest(BaseModel):
    """Схема для запроса описания таблицы или представления"""

    description: str = Field(..., description="Описание таблицы или представления")
    columns: Dict[str, Any] = Field(..., description="Описания колонок в формате column_descriptions.json")
    schema_name: str = Field(default="public", description="Имя схемы")
    object_type: str = Field(default="table", description="Тип объекта: table, view, generic")

    model_config = {
        "json_schema_extra": {
            "example": {
                "description": "Таблица продаж из кассовых систем",
                "schema_name": "public",
                "object_type": "table",
                "columns": {
                    "bill_date": {
                        "datatype": "date",
                        "placeholder": "2025-01-01",
                        "теги": "чек, дата",
                        "описание": "дата чека",
                    },
                    "goods_name": {
                        "datatype": "character varying",
                        "placeholder": "Батут SportsPower SP-4-10-020",
                        "теги": "товар, наименование",
                        "описание": "название товара",
                    },
                },
            }
        }
    }


class TableDescriptionResponse(BaseModel):
    """Ответ с описанием таблицы или представления"""

    success: bool = Field(..., description="Статус операции")
    database_name: str = Field(..., description="Имя базы данных")
    schema_name: str = Field(..., description="Имя схемы")
    table_name: str = Field(..., description="Имя таблицы или представления")
    object_type: str = Field(..., description="Тип объекта")
    description: Dict[str, Any] = Field(..., description="Описание объекта и колонок")


class DatabaseInfoResponse(BaseModel):
    """Информация о базе данных"""

    success: bool = Field(..., description="Статус получения информации")
    database_name: str = Field(..., description="Имя базы данных")
    is_connected: bool = Field(..., description="Статус подключения")
    saved_descriptions_count: int = Field(..., description="Количество сохраненных описаний")
