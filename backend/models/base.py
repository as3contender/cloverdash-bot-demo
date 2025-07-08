"""
Базовые схемы для основных запросов и ответов API
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime


class QueryRequest(BaseModel):
    """Запрос пользователя"""

    query: str = Field(..., description="Вопрос пользователя на естественном языке")
    user_id: Optional[str] = Field(None, description="ID пользователя")

    model_config = {
        "json_schema_extra": {
            "example": {"query": "Сколько пользователей зарегистрировалось за последний месяц?", "user_id": "user123"}
        }
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
