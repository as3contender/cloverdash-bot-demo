# CloverdashBot Backend

FastAPI backend для обработки запросов от Telegram-бота и генерации SQL запросов с помощью LLM.

## Архитектура

### Модульная структура

```
backend/
├── main.py                 # Точка входа приложения
├── config/
│   ├── __init__.py
│   └── settings.py        # Конфигурация и настройки
├── api/
│   ├── __init__.py
│   └── routes.py          # API эндпоинты
├── services/
│   ├── __init__.py
│   ├── database.py        # Сервис для работы с БД
│   └── llm_service.py     # Сервис для работы с LLM
├── models/
│   ├── __init__.py
│   └── schemas.py         # Pydantic модели
├── requirements.txt       # Зависимости
└── env_example.txt       # Пример конфигурации
```

### Компоненты

#### 🔧 **Config Module** (`config/`)
- **settings.py**: Централизованная конфигурация приложения
- Использует `pydantic-settings` для валидации переменных окружения
- Содержит настройки для OpenAI, базы данных, API и логирования

#### 🌐 **API Module** (`api/`)
- **routes.py**: Все HTTP эндпоинты
- Чистые роуты без бизнес-логики
- Обработка ошибок и валидация запросов

#### ⚙️ **Services Module** (`services/`)
- **llm_service.py**: Работа с OpenAI и генерация SQL
- **database.py**: Управление соединениями с БД и выполнение запросов
- Изолированная бизнес-логика

#### 📊 **Models Module** (`models/`)
- **schemas.py**: Pydantic модели для запросов и ответов
- Валидация данных и автодокументация API

## API Endpoints

### `GET /`
Информация о API

### `GET /health`
Проверка состояния сервиса и компонентов

**Ответ:**
```json
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": "2024-01-01T00:00:00",
  "version": "1.0.0",
  "database_connected": true
}
```

### `POST /query`
Обработка запроса пользователя

**Запрос:**
```json
{
  "question": "Сколько заказов было за последний месяц?",
  "user_id": "123456789",
  "context": {}
}
```

**Ответ:**
```json
{
  "answer": "За последний месяц было сделано 1,245 заказов",
  "sql_query": "SELECT COUNT(*) FROM orders WHERE created_at >= NOW() - INTERVAL '1 month'",
  "success": true,
  "execution_time": 1.23,
  "error_message": null
}
```

### `GET /schema`
Получение схемы базы данных

## Установка и запуск

### 1. Установка зависимостей
```bash
cd backend
pip install -r requirements.txt
```

### 2. Конфигурация
Создайте файл `.env` на основе `env_example.txt`:

```env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_HOST=localhost
DATABASE_PORT=5160
DATABASE_USER=postgress
DATABASE_PASSWORD=password
DATABASE_NAME=mydatabase
```

### 3. Запуск
```bash
python main.py
```

Или через uvicorn:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Разработка

### Логирование
Все компоненты используют структурированное логирование:
```python
import logging
logger = logging.getLogger(__name__)
```

### Добавление новых эндпоинтов
1. Создайте Pydantic модели в `models/schemas.py`
2. Добавьте роут в `api/routes.py`
3. При необходимости расширьте сервисы

### Добавление новых сервисов
1. Создайте новый файл в `services/`
2. Следуйте паттерну инициализации как в существующих сервисах
3. Импортируйте в `main.py` при необходимости

## Безопасность

### SQL Injection Protection
- Валидация всех SQL запросов
- Только SELECT операции
- Фильтрация запрещенных ключевых слов

### Environment Variables
- Все секреты в переменных окружения
- Использование `pydantic-settings` для валидации

## Мониторинг и отладка

### Health Check
Endpoint `/health` проверяет:
- Статус приложения
- Подключение к базе данных
- Время ответа

### Логи
- Структурированные логи с уровнями
- Логирование всех запросов и ошибок
- Метрики времени выполнения

## TODO
- [ ] Кэширование результатов запросов
- [ ] Метрики производительности
- [ ] Rate limiting
- [ ] Аутентификация и авторизация
- [ ] Более детальная валидация SQL
- [ ] Поддержка разных СУБД 