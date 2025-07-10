"""
Кастомные исключения для Telegram бота
"""


class BotException(Exception):
    """Базовое исключение для бота"""

    def __init__(self, message: str, user_id: str = None):
        self.message = message
        self.user_id = user_id
        super().__init__(self.message)


class AuthenticationError(BotException):
    """Ошибка аутентификации пользователя"""

    pass


class APIError(BotException):
    """Ошибка взаимодействия с Backend API"""

    def __init__(self, message: str, status_code: int = None, user_id: str = None):
        self.status_code = status_code
        super().__init__(message, user_id)


class ConfigurationError(BotException):
    """Ошибка конфигурации бота"""

    pass


class ValidationError(BotException):
    """Ошибка валидации пользовательского ввода"""

    pass


class CacheError(BotException):
    """Ошибка работы с кэшем"""

    pass


class FormattingError(BotException):
    """Ошибка форматирования сообщений"""

    pass


class TranslationError(BotException):
    """Ошибка получения переводов"""

    pass


class NetworkError(BotException):
    """Ошибка сетевого взаимодействия"""

    def __init__(self, message: str, timeout: bool = False, user_id: str = None):
        self.timeout = timeout
        super().__init__(message, user_id)


class DatabaseConnectionError(BotException):
    """Ошибка подключения к базе данных"""

    pass


class QueryExecutionError(BotException):
    """Ошибка выполнения запроса к базе данных"""

    def __init__(self, message: str, sql_query: str = None, user_id: str = None):
        self.sql_query = sql_query
        super().__init__(message, user_id)
