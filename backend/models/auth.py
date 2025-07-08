"""
Схемы для аутентификации и управления пользователями
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Базовая схема пользователя"""

    username: Optional[str] = Field(None, description="Имя пользователя")
    email: Optional[str] = Field(None, description="Email пользователя")
    full_name: Optional[str] = Field(None, description="Полное имя пользователя")
    telegram_id: Optional[str] = Field(None, description="Telegram ID пользователя")
    telegram_username: Optional[str] = Field(None, description="Telegram username")


class UserCreate(UserBase):
    """Схема для создания пользователя"""

    password: Optional[str] = Field(None, description="Пароль пользователя")


class UserUpdate(BaseModel):
    """Схема для обновления пользователя"""

    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None


class User(UserBase):
    """Схема пользователя (ответ)"""

    id: str = Field(..., description="ID пользователя")
    is_active: bool = Field(True, description="Активен ли пользователь")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата обновления")

    model_config = {"from_attributes": True}


class TelegramAuth(BaseModel):
    """Схема для авторизации через Telegram"""

    telegram_id: str = Field(..., description="Telegram ID пользователя")
    telegram_username: Optional[str] = Field(None, description="Telegram username")
    first_name: Optional[str] = Field(None, description="Имя пользователя в Telegram")
    last_name: Optional[str] = Field(None, description="Фамилия пользователя в Telegram")


class Token(BaseModel):
    """Схема токена"""

    access_token: str = Field(..., description="JWT токен доступа")
    token_type: str = Field("bearer", description="Тип токена")
    expires_in: Optional[int] = Field(None, description="Время жизни токена в секундах")


class TokenData(BaseModel):
    """Данные токена"""

    user_id: Optional[str] = None


class LoginRequest(BaseModel):
    """Схема для входа в систему"""

    username: str = Field(..., description="Email или username")
    password: str = Field(..., description="Пароль")


class UserQueryHistory(BaseModel):
    """Схема для истории запросов пользователя"""

    original_query: str = Field(..., description="Оригинальный запрос пользователя")
    sql_query: Optional[str] = Field(None, description="Сгенерированный SQL запрос")
    result_count: int = Field(default=0, description="Количество строк в результате")
    execution_time: float = Field(default=0.0, description="Время выполнения")
    success: bool = Field(..., description="Успешность выполнения")
    error_message: Optional[str] = Field(None, description="Сообщение об ошибке")
    created_at: datetime = Field(..., description="Время создания запроса")


class UserSettings(BaseModel):
    """Схема настроек пользователя"""

    preferred_language: str = Field(default="en", description="Предпочитаемый язык")
    show_explanation: bool = Field(default=True, description="Показывать объяснение")
    show_sql: bool = Field(default=False, description="Показывать SQL запрос")
    timezone: str = Field(default="UTC", description="Временная зона")
    query_limit: int = Field(default=100, description="Лимит запросов")
    settings_json: dict = Field(default={}, description="Дополнительные настройки в JSON")


class UserSettingsUpdate(BaseModel):
    """Обновление настроек пользователя"""

    preferred_language: Optional[str] = None
    show_explanation: Optional[bool] = None
    show_sql: Optional[bool] = None


class UserPermission(BaseModel):
    """Схема разрешений пользователя"""

    permission_name: str = Field(..., description="Название разрешения")
    granted: bool = Field(default=True, description="Предоставлено ли разрешение")
    granted_by: Optional[str] = Field(None, description="Кем предоставлено")
    granted_at: datetime = Field(..., description="Когда предоставлено")
