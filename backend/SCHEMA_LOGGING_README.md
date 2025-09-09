# Система логирования схем базы данных

Эта система предоставляет комплексное логирование и мониторинг доступа к схемам базы данных (`schema_name`) и доступным для пользователей таблицам.

## 📁 Файлы системы

### Основные модули

1. **`schema_validation_logger.py`** - Основной модуль для валидации и логирования схем
2. **`schema_monitoring.py`** - Модуль мониторинга в реальном времени
3. **`schema_logging_integration.py`** - Интеграция с существующими API endpoints
4. **`test_schema_logging.py`** - Тестовый скрипт для проверки функциональности

## 🚀 Быстрый старт

### 1. Базовое использование

```python
from schema_validation_logger import SchemaValidationLogger

# Создаем валидатор
validator = SchemaValidationLogger()

# Проверяем доступ пользователя к схемам
result = await validator.validate_schema_access("user_id", "database_name")
```

### 2. Мониторинг в реальном времени

```python
from schema_monitoring import schema_monitor

# Логируем доступ к схеме
schema_monitor.log_schema_access(
    user_id="user1",
    schema_name="public", 
    table_name="users",
    access_type="read",
    success=True
)

# Получаем статистику пользователя
stats = schema_monitor.get_user_schema_stats("user1")
```

### 3. Использование декоратора

```python
from schema_monitoring import log_schema_access

@log_schema_access("schema_name", "table_name")
async def my_function(user_id: str, schema_name: str, table_name: str):
    # Ваш код здесь
    return result
```

## 📊 Функциональность

### Валидация схем

Система проверяет:
- ✅ Доступность схем для пользователей
- ✅ Соответствие `schema_name` с фактически доступными таблицами
- ✅ Права доступа к схемам
- ✅ Проблемы с правами доступа

### Логирование

Система логирует:
- 🔍 Все обращения к схемам
- 📊 Статистику использования схем
- ⚠️ Ошибки доступа к схемам
- 📋 Отчеты по доступности схем

### Мониторинг

Система отслеживает:
- 👥 Активность пользователей по схемам
- 📈 Статистику успешности доступа
- 🏆 Топ схем по использованию
- 📅 Ежедневные отчеты

## 🔧 Настройка

### 1. Инициализация в приложении

Добавьте в ваш `main.py` или точку входа:

```python
from schema_logging_integration import initialize_schema_logging

# Инициализируем логирование схем
initialize_schema_logging()
```

### 2. Настройка логирования

```python
import logging

# Настройка уровня логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('schema_validation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
```

## 📋 API Endpoints

Система автоматически добавляет логирование в существующие endpoints:

### `/api/database/tables`
- Логирует доступные схемы для пользователя
- Отслеживает обращения к списку таблиц

### `/api/database/table/{table_name}/sample`
- Логирует доступ к конкретным таблицам
- Отслеживает успешность получения образцов данных

## 🧪 Тестирование

### Запуск тестов

```bash
cd backend
python test_schema_logging.py
```

### Результаты тестирования

Тесты проверяют:
1. ✅ Базовый мониторинг схем
2. ✅ Валидацию схем
3. ✅ Интеграцию с сервисами
4. ✅ Декоратор логирования
5. ✅ Операции с файлами

## 📊 Примеры логов

### Успешный доступ к схеме

```
2025-01-27 10:30:15 - schema_monitoring - INFO - ✅ СХЕМА: Пользователь user1 | Схема: public | Таблица: users | Тип: read | Время: 10:30:15
```

### Ошибка доступа к схеме

```
2025-01-27 10:30:20 - schema_monitoring - WARNING - ⚠️ НЕУДАЧНЫЙ ДОСТУП: Пользователь user2 не смог получить доступ к таблице public.orders
```

### Отчет по схемам

```
2025-01-27 10:30:25 - schema_validation_logger - INFO - 📋 РЕЗУЛЬТАТЫ ПРОВЕРКИ СХЕМ ДЛЯ ПОЛЬЗОВАТЕЛЯ user1
2025-01-27 10:30:25 - schema_validation_logger - INFO - 🗄️ База данных: demo_db
2025-01-27 10:30:25 - schema_validation_logger - INFO - ✅ Доступные схемы (2): ['public', 'demo1']
```

## 📈 Мониторинг и отчеты

### Ежедневный отчет

```python
from schema_monitoring import schema_monitor

# Генерируем ежедневный отчет
schema_monitor.log_daily_schema_report()
```

### Статистика пользователя

```python
# Получаем статистику конкретного пользователя
stats = schema_monitor.get_user_schema_stats("user1")
print(f"Схемы: {stats['schemas_accessed']}")
print(f"Всего обращений: {stats['total_access_count']}")
```

### Сохранение результатов

```python
from schema_validation_logger import SchemaValidationLogger

validator = SchemaValidationLogger()
results = await validator.validate_multiple_users(["user1", "user2"], "database")
validator.save_results_to_file(results, "schema_report.json")
```

## 🔍 Отладка

### Проверка подключения к БД

```python
from services.app_database import app_database_service
from services.data_database import data_database_service

print(f"App DB подключена: {app_database_service.is_connected}")
print(f"Data DB подключена: {data_database_service.is_connected}")
```

### Ручная проверка схем

```python
from schema_logging_integration import generate_schema_report

# Генерируем отчет для конкретного пользователя
report = await generate_schema_report(user_id="user1", database_name="demo_db")
print(report)
```

## ⚠️ Устранение неполадок

### Проблема: "База описаний недоступна"

**Решение:**
1. Проверьте подключение к базе данных приложения
2. Убедитесь, что таблица `database_descriptions` существует
3. Проверьте права доступа к базе данных

### Проблема: "Схема не найдена"

**Решение:**
1. Проверьте правильность имени схемы
2. Убедитесь, что у пользователя есть права доступа к схеме
3. Проверьте таблицу `user_permissions` (если используется)

### Проблема: "Ошибка при применении патча"

**Решение:**
1. Убедитесь, что все модули импортированы корректно
2. Проверьте, что API endpoints существуют
3. Проверьте версии зависимостей

## 📝 Конфигурация

### Переменные окружения

```bash
# Уровень логирования
SCHEMA_LOG_LEVEL=INFO

# Файл логов
SCHEMA_LOG_FILE=schema_validation.log

# Включение детального логирования
SCHEMA_DETAILED_LOGGING=true
```

### Настройка в коде

```python
# Настройка мониторинга
from schema_monitoring import schema_monitor

# Включение детального логирования
schema_monitor.detailed_logging = True

# Настройка кэширования
schema_monitor.cache_ttl = 3600  # 1 час
```

## 🔄 Интеграция с существующими системами

### FastAPI

```python
from fastapi import FastAPI
from schema_logging_integration import initialize_schema_logging

app = FastAPI()

# Инициализируем логирование схем
initialize_schema_logging()

@app.on_event("startup")
async def startup_event():
    # Дополнительная инициализация
    pass
```

### Telegram Bot

```python
# В handlers.py или аналогичном файле
from schema_monitoring import schema_monitor

async def handle_database_query(user_id: str, query: str):
    # Логируем обращение к базе данных
    schema_monitor.log_schema_access(
        user_id=user_id,
        schema_name="public",  # или извлечь из query
        table_name="unknown",
        access_type="query",
        success=True
    )
```

## 📚 Дополнительные ресурсы

- [Документация по API базы данных](api/database.py)
- [Сервис работы с БД приложения](services/app_database.py)
- [Сервис работы с данными](services/data_database.py)
- [LLM сервис](services/llm_service.py)

## 🤝 Поддержка

При возникновении проблем:

1. Проверьте логи в файле `schema_validation.log`
2. Запустите тесты: `python test_schema_logging.py`
3. Проверьте подключение к базам данных
4. Убедитесь в корректности прав доступа

---

**Версия:** 1.0.0  
**Дата создания:** 2025-01-27  
**Автор:** CloverDash Bot System
