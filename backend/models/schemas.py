from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class QueryRequest(BaseModel):
    """Модель запроса пользователя"""

    question: str = Field(..., description="Вопрос пользователя на естественном языке")
    user_id: Optional[str] = Field(None, description="ID пользователя")
    context: Optional[dict] = Field(None, description="Дополнительный контекст")


class QueryResponse(BaseModel):
    """Модель ответа на запрос"""

    answer: str = Field(..., description="Ответ на вопрос пользователя")
    sql_query: Optional[str] = Field(None, description="Сгенерированный SQL запрос")
    success: bool = Field(..., description="Успешность выполнения запроса")
    execution_time: Optional[float] = Field(None, description="Время выполнения в секундах")
    error_message: Optional[str] = Field(None, description="Сообщение об ошибке")


class DatabaseQueryResult(BaseModel):
    """Модель результата выполнения SQL запроса"""

    data: List[dict] = Field(..., description="Результаты запроса")
    columns: List[str] = Field(..., description="Названия колонок")
    row_count: int = Field(..., description="Количество строк")
    execution_time: float = Field(..., description="Время выполнения запроса")


class HealthResponse(BaseModel):
    """Модель ответа health check"""

    status: str = Field(..., description="Статус сервиса")
    timestamp: datetime = Field(..., description="Время проверки")
    version: str = Field(..., description="Версия API")
    database_connected: bool = Field(..., description="Статус подключения к БД")


class ErrorResponse(BaseModel):
    """Модель ошибки"""

    error: str = Field(..., description="Описание ошибки")
    error_code: Optional[str] = Field(None, description="Код ошибки")
    details: Optional[dict] = Field(None, description="Дополнительные детали ошибки")
