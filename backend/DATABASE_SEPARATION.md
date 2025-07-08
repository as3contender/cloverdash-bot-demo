# Разделение баз данных

## Обзор

В системе CloverdashBot реализовано разделение на две отдельные базы данных:

1. **Application Database** - база данных приложения
2. **Data Database** - база данных пользовательских данных

## Архитектура

### Application Database (app_database)
**Назначение**: Хранение системных данных приложения
**Сервис**: `app_database_service`
**Содержимое**:
- Пользователи и аутентификация (`users`)
- История запросов (`query_history`)
- Настройки пользователей (`user_settings`)
- Права и разрешения (`user_permissions`)

### Data Database (data_database)
**Назначение**: Хранение пользовательских данных для аналитики
**Сервис**: `data_database_service`
**Содержимое**:
- Бизнес-данные пользователей
- Таблицы для SQL-запросов
- Только READ-доступ через API

## Преимущества разделения

### 1. Безопасность
- **Изоляция данных**: Системные данные (пользователи, пароли) отделены от бизнес-данных
- **Ограниченный доступ**: К data database разрешены только SELECT запросы
- **Независимые права доступа**: Разные credentials для разных баз

### 2. Масштабируемость
- **Независимое масштабирование**: Каждая база может масштабироваться отдельно
- **Различные ресурсы**: Application DB может быть меньше, Data DB - больше
- **Раздельное резервное копирование**: Разные стратегии backup для разных типов данных

### 3. Производительность
- **Снижение нагрузки**: Разделение read/write операций
- **Оптимизация**: Каждая база оптимизирована под свои задачи
- **Кэширование**: Возможность разных стратегий кэширования

### 4. Управление
- **Разделение ответственности**: Разные команды могут управлять разными базами
- **Версионирование**: Независимые схемы и миграции
- **Мониторинг**: Раздельный мониторинг производительности

## Конфигурация

### Environment Variables

```bash
# Application Database (пользователи, история, настройки)
APP_DATABASE_URL=postgresql://app_user:app_password@localhost:5432/cloverdash_app
APP_DATABASE_HOST=localhost
APP_DATABASE_PORT=5432
APP_DATABASE_USER=app_user
APP_DATABASE_PASSWORD=app_password
APP_DATABASE_NAME=cloverdash_app

# Data Database (пользовательские данные для запросов)
DATA_DATABASE_URL=postgresql://data_user:data_password@localhost:5433/cloverdash_data
DATA_DATABASE_HOST=localhost
DATA_DATABASE_PORT=5433
DATA_DATABASE_USER=data_user
DATA_DATABASE_PASSWORD=data_password
DATA_DATABASE_NAME=cloverdash_data

# Legacy (для обратной совместимости)
DATABASE_URL=postgresql://user:password@localhost:5432/database_name
```

### Fallback Logic
Если специфичные настройки не найдены, система использует legacy настройки:
1. Сначала проверяются `APP_DATABASE_*` параметры
2. Если не найдены, используются `DATABASE_*` параметры
3. То же самое для `DATA_DATABASE_*`

## Сервисы

### AppDatabaseService
```python
from services.app_database import app_database_service

# Инициализация
await app_database_service.initialize()

# Работа с пользователями (через user_service)
user = await user_service.get_user_by_id(user_id)

# Сохранение истории
await user_service.save_user_query_history(...)
```

### DataDatabaseService
```python
from services.data_database import data_database_service

# Инициализация
await data_database_service.initialize()

# Выполнение запросов (только SELECT)
result = await data_database_service.execute_query("SELECT * FROM customers LIMIT 10")

# Получение схемы
schema = await data_database_service.get_database_schema()
```

## API Endpoints

### Application Database
Управляется через:
- `/auth/*` - аутентификация и регистрация
- `/database/history` - история запросов пользователя

### Data Database
Доступ через:
- `/database/query` - выполнение SQL через LLM
- `/database/schema` - получение схемы данных
- `/database/sql` - прямые SQL запросы (только SELECT)

## Миграция с единой базы

При миграции с единой базы данных:

1. **Сохранение совместимости**: Legacy настройки DATABASE_* продолжают работать
2. **Постепенный переход**: Можно настроить APP_ и DATA_ параметры постепенно
3. **Автоматический fallback**: Если новые настройки не найдены, используются старые

## Мониторинг

### Health Check
```bash
GET /health/
```

Возвращает статус обеих баз данных:
```json
{
  "status": "healthy",
  "database_connected": true,
  "llm_service_available": true
}
```

### Detailed Info
```bash
GET /health/info
```

Подробная информация о каждой базе:
```json
{
  "databases": {
    "application_db": {
      "connected": true,
      "service": "Application Database Service",
      "description": "Пользователи, история, настройки"
    },
    "data_db": {
      "connected": true,
      "service": "Data Database Service", 
      "description": "Пользовательские данные для запросов"
    }
  }
}
```

## Лучшие практики

### 1. Безопасность
- Используйте разные credentials для каждой базы
- Ограничьте сетевой доступ между базами
- Настройте firewall правила

### 2. Резервное копирование
- Application DB: Частое резервное копирование (содержит пользователей)
- Data DB: Может быть реже (только бизнес-данные)

### 3. Мониторинг
- Отдельные метрики для каждой базы
- Алерты при недоступности любой из баз
- Мониторинг производительности запросов

### 4. Разработка
- Используйте разные базы данных в development/staging
- Тестируйте fallback логику
- Документируйте схемы обеих баз данных 