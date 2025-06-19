# Тесты для CloverdashBot Backend

Comprehensive система тестирования для backend API с разделением по компонентам и типам тестов.

## 🏗️ Структура тестов

```
tests/
├── __init__.py
├── conftest.py              # Общие фикстуры и настройки
├── test_database.py         # Тесты для сервиса базы данных
├── test_llm_service.py      # Тесты для сервиса LLM
├── test_api.py             # Тесты для API endpoints
├── test_utils.py           # Утилиты для запуска тестов
└── README.md               # Документация тестов
```

## 🏷️ Маркеры тестов

Тесты организованы с помощью pytest маркеров:

- **`@pytest.mark.unit`** - Unit тесты (изолированные компоненты)
- **`@pytest.mark.integration`** - Integration тесты (взаимодействие компонентов)
- **`@pytest.mark.database`** - Тесты базы данных
- **`@pytest.mark.llm`** - Тесты LLM сервиса
- **`@pytest.mark.api`** - Тесты API endpoints

## 🚀 Запуск тестов

### Быстрый старт
```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск всех тестов
make test
# или
python -m pytest

# С покрытием кода
make test-coverage
```

### Запуск по типам

```bash
# Unit тесты
make test-unit
python -m pytest -m unit

# Integration тесты  
make test-integration
python -m pytest -m integration

# Database тесты
make test-database
python -m pytest -m database

# LLM тесты
make test-llm
python -m pytest -m llm

# API тесты
make test-api
python -m pytest -m api
```

### Дополнительные опции

```bash
# Подробный вывод
python -m pytest -v

# Остановка на первой ошибке
python -m pytest -x

# Запуск конкретного теста
python -m pytest tests/test_api.py::TestAPIEndpoints::test_root_endpoint

# Запуск с профилированием
python -m pytest --durations=10
```

## 📊 Coverage отчеты

```bash
# HTML отчет (откроется в браузере)
make test-coverage
open htmlcov/index.html

# Терминальный отчет
python -m pytest --cov=. --cov-report=term-missing

# Установка минимального покрытия
python -m pytest --cov=. --cov-fail-under=80
```

## 🧪 Типы тестов

### 1. Database тесты (`test_database.py`)

Тестируют сервис работы с базой данных:

- ✅ Инициализация соединений
- ✅ Выполнение SQL запросов
- ✅ Получение схемы базы данных
- ✅ Обработка ошибок соединения
- ✅ Контекстные менеджеры
- ✅ Lifecycle управление

**Примеры:**
```python
async def test_execute_query_success(database_service_mock):
    result = await service.execute_query("SELECT * FROM users;")
    assert result.row_count == 2
    assert result.columns == ["id", "name", "email"]
```

### 2. LLM тесты (`test_llm_service.py`)

Тестируют сервис работы с OpenAI:

- ✅ Генерация SQL запросов
- ✅ Валидация SQL на безопасность
- ✅ Очистка от markdown форматирования
- ✅ Обработка ошибок API
- ✅ Производительность
- ✅ Граничные случаи

**Примеры:**
```python
async def test_generate_sql_query_success(llm_service_mock):
    sql_query, time = service.generate_sql_query("Сколько пользователей?")
    assert sql_query == "SELECT COUNT(*) FROM users;"
    assert service.validate_sql_query(sql_query) is True
```

### 3. API тесты (`test_api.py`)

Тестируют HTTP endpoints:

- ✅ **GET /** - основная информация
- ✅ **GET /health** - проверка состояния
- ✅ **POST /query** - обработка запросов
- ✅ **GET /schema** - схема базы данных
- ✅ Валидация запросов/ответов
- ✅ Обработка ошибок
- ✅ CORS настройки

**Примеры:**
```python
async def test_query_endpoint_success(test_client):
    response = await test_client.post("/query", json={
        "question": "Сколько пользователей?",
        "user_id": "test_user"
    })
    assert response.status_code == 200
    assert response.json()["success"] is True
```

## 🛠️ Фикстуры

### Основные фикстуры (в `conftest.py`)

- **`test_client`** - HTTP клиент для API тестов
- **`database_service_mock`** - мок сервиса БД
- **`llm_service_mock`** - мок LLM сервиса
- **`sample_db_result`** - примеры результатов запросов
- **`mock_openai_response`** - мок ответов OpenAI

### Использование фикстур

```python
async def test_example(test_client, database_service_mock):
    # test_client готов для HTTP запросов
    # database_service_mock готов для мокирования БД
    response = await test_client.get("/health")
    assert response.status_code == 200
```

## 🎯 Стратегия тестирования

### Unit тесты
- Тестируют изолированные функции и методы
- Используют моки для внешних зависимостей
- Быстрые и детерминированные

### Integration тесты  
- Тестируют взаимодействие между компонентами
- Проверяют полные workflow'ы
- Используют реальные сервисы (где возможно)

### API тесты
- Тестируют HTTP endpoints end-to-end
- Проверяют валидацию запросов/ответов
- Тестируют обработку ошибок

## 📋 Чек-лист для добавления тестов

При добавлении новой функциональности:

- [ ] Добавить unit тесты для новых функций
- [ ] Добавить integration тесты для workflow
- [ ] Обновить API тесты при изменении endpoints
- [ ] Проверить покрытие кода (`make test-coverage`)
- [ ] Убедиться, что все тесты проходят (`make test`)
- [ ] Добавить новые фикстуры если нужно

## 🐛 Отладка тестов

### Часто встречающиеся проблемы

1. **Тест падает с async ошибкой**
   ```bash
   # Убедитесь, что используете @pytest.mark.asyncio
   @pytest.mark.asyncio
   async def test_example():
       pass
   ```

2. **Мок не работает**
   ```python
   # Проверьте правильность пути для патча
   with patch('api.routes.database_service.test_connection'):
       # правильный путь: module.где.используется.функция
   ```

3. **Fixture не найдена**
   ```python
   # Убедитесь, что фикстура определена в conftest.py
   # или импортирована в тестовом файле
   ```

### Полезные команды для отладки

```bash
# Запуск с детальным выводом
python -m pytest -vvv -s

# Запуск конкретного теста с выводом print
python -m pytest tests/test_api.py::test_name -s

# Запуск с профилированием
python -m pytest --durations=0

# Запуск в режиме PDB при ошибке
python -m pytest --pdb
```

## 📈 Метрики качества

Цели покрытия тестами:
- **Общее покрытие**: ≥ 80%
- **API endpoints**: ≥ 90%
- **Core services**: ≥ 85%
- **Error handling**: ≥ 70%

## 🔧 CI/CD

```bash
# Команды для CI/CD пайплайна
make ci-test    # Тесты + coverage + XML отчет
make ci-lint    # Линтинг кода
```

## 📚 Дополнительная информация

- [pytest документация](https://docs.pytest.org/)
- [pytest-asyncio документация](https://pytest-asyncio.readthedocs.io/)
- [httpx тестирование](https://www.python-httpx.org/advanced/#testing)
- [FastAPI тестирование](https://fastapi.tiangolo.com/tutorial/testing/) 