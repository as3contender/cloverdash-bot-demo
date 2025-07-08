"""
Модели данных для CloverdashBot Backend

Структура:
- base.py: Базовые схемы запросов и ответов
- auth.py: Схемы аутентификации и пользователей
- database.py: Схемы для работы с базой данных
- llm.py: Схемы для работы с LLM сервисом
"""

# Импортируем все схемы из модулей
from .base import *
from .auth import *
from .database import *
from .llm import *

# Экспортируем все для удобства импорта
__all__ = [
    # Базовые схемы (base.py)
    "QueryRequest",
    "QueryResponse",
    "HealthResponse",
    # Схемы базы данных (database.py)
    "SchemaResponse",
    "DatabaseQueryResult",
    "TableDescriptionRequest",
    "TableDescriptionResponse",
    "DatabaseInfoResponse",
    # Схемы аутентификации (auth.py)
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "User",
    "TelegramAuth",
    "Token",
    "TokenData",
    "LoginRequest",
    "UserQueryHistory",
    "UserSettings",
    "UserPermission",
    # Схемы LLM (llm.py)
    "LLMQueryRequest",
    "LLMQueryResponse",
    "LLMServiceInfo",
    "LLMConnectionTest",
    "SQLValidationResult",
]
