"""
Схемы для работы с LLM сервисом
"""

from pydantic import BaseModel, Field
from typing import Optional


class LLMQueryRequest(BaseModel):
    """Запрос к LLM сервису"""

    natural_query: str = Field(..., description="Запрос на естественном языке")
    context: Optional[str] = Field(None, description="Дополнительный контекст")


class LLMQueryResponse(BaseModel):
    """Ответ от LLM сервиса"""

    sql_query: str = Field(..., description="Сгенерированный SQL запрос")
    explanation: str = Field(..., description="Объяснение запроса")
    execution_time: float = Field(..., description="Время выполнения")

    model_config = {
        "json_schema_extra": {
            "example": {
                "sql_query": "SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '1 month';",
                "explanation": "Этот запрос подсчитывает количество пользователей, зарегистрированных за последний месяц.",
                "execution_time": 1.23,
            }
        }
    }


class LLMServiceInfo(BaseModel):
    """Информация о LLM сервисе"""

    service_name: str = Field(..., description="Название сервиса")
    llm_model_name: str = Field(..., description="Используемая модель")
    provider: str = Field(..., description="Провайдер (OpenAI, Anthropic, etc.)")
    available: bool = Field(..., description="Доступность сервиса")
    last_check: Optional[str] = Field(None, description="Время последней проверки")


class LLMConnectionTest(BaseModel):
    """Результат тестирования подключения к LLM"""

    success: bool = Field(..., description="Успешность подключения")
    response_time: float = Field(..., description="Время ответа в секундах")
    error_message: Optional[str] = Field(None, description="Сообщение об ошибке")
    llm_model_info: Optional[dict] = Field(None, description="Информация о модели")


class SQLValidationResult(BaseModel):
    """Результат валидации SQL запроса"""

    is_valid: bool = Field(..., description="Валиден ли SQL запрос")
    is_safe: bool = Field(..., description="Безопасен ли SQL запрос")
    error_message: Optional[str] = Field(None, description="Сообщение об ошибке")
    security_warnings: list = Field(default=[], description="Предупреждения безопасности")
