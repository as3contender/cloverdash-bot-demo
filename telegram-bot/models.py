from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from enum import Enum


class Language(Enum):
    """Поддерживаемые языки"""

    ENGLISH = "en"
    RUSSIAN = "ru"


class ObjectType(Enum):
    """Типы объектов базы данных"""

    TABLE = "table"
    VIEW = "view"


@dataclass
class UserData:
    """Данные пользователя из Telegram"""

    user_id: str
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]

    @classmethod
    def from_telegram_user(cls, user) -> "UserData":
        """Создание из объекта Telegram User"""
        return cls(user_id=str(user.id), username=user.username, first_name=user.first_name, last_name=user.last_name)


@dataclass
class UserSettings:
    """Настройки пользователя"""

    preferred_language: Language = Language.ENGLISH
    show_explanation: bool = True
    show_sql: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserSettings":
        """Создание из словаря"""
        return cls(
            preferred_language=Language(data.get("preferred_language", "en")),
            show_explanation=data.get("show_explanation", True),
            show_sql=data.get("show_sql", False),
        )


@dataclass
class DatabaseTable:
    """Информация о таблице базы данных"""

    full_name: str
    schema_name: str
    table_name: str
    object_type: ObjectType
    description: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatabaseTable":
        """Создание из словаря"""
        return cls(
            full_name=data["full_name"],
            schema_name=data["schema_name"],
            table_name=data["table_name"],
            object_type=ObjectType(data["object_type"]),
            description=data.get("description"),
        )


@dataclass
class QueryResult:
    """Результат выполнения запроса"""

    success: bool
    message: str
    data: List[Dict[str, Any]]
    sql_query: Optional[str] = None
    explanation: Optional[str] = None
    execution_time: Optional[float] = None
    row_count: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QueryResult":
        """Создание из словаря"""
        return cls(
            success=data.get("success", False),
            message=data.get("message", ""),
            data=data.get("data", []),
            sql_query=data.get("sql_query"),
            explanation=data.get("explanation"),
            execution_time=data.get("execution_time"),
            row_count=data.get("row_count", len(data.get("data", []))),
        )


@dataclass
class APIResponse:
    """Базовый класс для ответов API"""

    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "APIResponse":
        """Создание из словаря"""
        return cls(success=data.get("success", False), message=data.get("message", ""), data=data.get("data"))


@dataclass
class ProcessingMessage:
    """Информация о сообщении "обработка запроса" """

    message_id: int
    chat_id: int
    text: str
