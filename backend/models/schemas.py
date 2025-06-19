from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime


class QueryRequest(BaseModel):
    """Запрос пользователя"""

    query: str = Field(..., description="Вопрос пользователя на естественном языке")
    user_id: Optional[str] = Field(None, description="ID пользователя")

    class Config:
        schema_extra = {
            "example": {"query": "Сколько пользователей зарегистрировалось за последний месяц?", "user_id": "user123"}
        }


class QueryResponse(BaseModel):
    """Ответ на запрос пользователя"""

    success: bool = Field(..., description="Статус выполнения запроса")
    message: str = Field(..., description="Сообщение о результате")
    sql_query: Optional[str] = Field(None, description="Сгенерированный SQL запрос")
    explanation: Optional[str] = Field(None, description="Объяснение запроса")
    data: List[Dict[str, Any]] = Field(default=[], description="Данные из базы")
    columns: List[str] = Field(default=[], description="Названия колонок")
    row_count: int = Field(default=0, description="Количество строк")
    execution_time: float = Field(default=0.0, description="Общее время выполнения")
    llm_time: float = Field(default=0.0, description="Время работы LLM")
    db_time: float = Field(default=0.0, description="Время работы с БД")


class HealthResponse(BaseModel):
    """Ответ проверки состояния сервиса"""

    status: str = Field(..., description="Общий статус сервиса")
    database_connected: bool = Field(..., description="Статус подключения к БД")
    llm_service_available: bool = Field(..., description="Доступность LLM сервиса")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now, description="Время проверки")


class SchemaResponse(BaseModel):
    """Ответ со схемой базы данных"""

    success: bool = Field(..., description="Статус получения схемы")
    message: str = Field(..., description="Сообщение о результате")
    schema: Dict[str, Any] = Field(..., description="Схема базы данных")
    table_count: int = Field(..., description="Количество таблиц")


class DatabaseQueryResult(BaseModel):
    """Результат выполнения SQL запроса"""

    data: List[Dict[str, Any]] = Field(..., description="Данные результата")
    columns: List[str] = Field(..., description="Названия колонок")
    row_count: int = Field(..., description="Количество строк")
    execution_time: float = Field(..., description="Время выполнения запроса")

    class Config:
        schema_extra = {
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


class LLMQueryRequest(BaseModel):
    """Запрос к LLM сервису"""

    natural_query: str = Field(..., description="Запрос на естественном языке")
    context: Optional[str] = Field(None, description="Дополнительный контекст")


class LLMQueryResponse(BaseModel):
    """Ответ от LLM сервиса"""

    sql_query: str = Field(..., description="Сгенерированный SQL запрос")
    explanation: str = Field(..., description="Объяснение запроса")
    execution_time: float = Field(..., description="Время выполнения")
    model_used: str = Field(..., description="Использованная модель")

    class Config:
        schema_extra = {
            "example": {
                "sql_query": "SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '1 month';",
                "explanation": "Этот запрос подсчитывает количество пользователей, зарегистрированных за последний месяц.",
                "execution_time": 1.23,
                "model_used": "gpt-3.5-turbo",
            }
        }
