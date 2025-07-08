# Управление описаниями таблиц базы данных

Эта функциональность позволяет сохранять и управлять описаниями таблиц и колонок базы данных пользовательских данных (data_database) в формате, совместимом с `column_descriptions.json`.

## Архитектура

### База данных
- **Таблица**: `database_descriptions` в app_database (база данных приложения)
- **Поля**:
  - `id` - UUID, первичный ключ
  - `database_name` - имя базы данных
  - `table_name` - имя таблицы
  - `table_description` - JSONB с описанием таблицы и колонок
  - `created_at` - дата создания
  - `updated_at` - дата обновления
  - Уникальный индекс: `(database_name, table_name)`

### Сервисы
- **app_database_service**: методы для работы с описаниями таблиц
- **data_database_service**: интеграция с сохраненными описаниями при получении схемы

## API Endpoints

### Управление описаниями таблиц

#### Сохранение описания таблицы
```
POST /descriptions/table/{database_name}/{table_name}
```

**Тело запроса** (формат column_descriptions.json):
```json
{
  "description": "Описание таблицы продаж",
  "columns": {
    "bill_date": {
      "datatype": "date",
      "placeholder": "2025-01-01",
      "теги": "чек, дата",
      "описание": "дата чека"
    },
    "goods_name": {
      "datatype": "character varying",
      "placeholder": "Батут SportsPower SP-4-10-020",
      "теги": "товар, наименование",
      "описание": "название товара"
    }
  }
}
```

#### Получение описания таблицы
```
GET /descriptions/table/{database_name}/{table_name}
```

#### Получение всех описаний базы данных
```
GET /descriptions/database/{database_name}
```

#### Получение всех описаний
```
GET /descriptions/all
```

#### Удаление описания таблицы
```
DELETE /descriptions/table/{database_name}/{table_name}
```

### Дополнительные endpoints

#### Импорт из column_descriptions.json
```
POST /descriptions/import/column-descriptions?database_name=mydb&table_name=sales
```
Импортирует описания из существующего `column_descriptions.json` в базу данных.

#### Информация о текущей базе данных
```
GET /descriptions/current-data-database
```
Возвращает информацию о подключенной базе данных пользовательских данных.

## Использование в коде

### Сохранение описания
```python
from services.app_database import app_database_service

# Описание в формате column_descriptions.json
description = {
    "description": "Таблица продаж",
    "columns": {
        "bill_date": {
            "datatype": "date",
            "placeholder": "2025-01-01",
            "теги": "чек, дата",
            "описание": "дата чека"
        }
    }
}

success = await app_database_service.save_table_description(
    "mydatabase", "sales", description
)
```

### Получение описания
```python
description = await app_database_service.get_table_description(
    "mydatabase", "sales"
)
```

### Получение всех описаний
```python
# Для конкретной базы данных
descriptions = await app_database_service.get_all_table_descriptions("mydatabase")

# Для всех баз данных
all_descriptions = await app_database_service.get_all_table_descriptions()
```

## Интеграция с data_database_service

При вызове `data_database_service.get_database_schema()` описания автоматически добавляются к информации о колонках:

1. **Приоритет 1**: Сохраненные описания из таблицы `database_descriptions`
2. **Приоритет 2**: Legacy описания из `column_descriptions.json` (fallback)

```python
schema = await data_database_service.get_database_schema()
# Возвращает схему с дополненными описаниями колонок
```

## Импорт данных

### Через API
```bash
curl -X POST "http://localhost:8000/descriptions/import/column-descriptions?database_name=mydb&table_name=sales" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Через скрипт
```bash
# Импорт описаний из column_descriptions.json
python import_descriptions.py import

# Просмотр текущих описаний
python import_descriptions.py list
```

## Формат данных

### Структура описания таблицы
```json
{
  "description": "Человекочитаемое описание таблицы",
  "columns": {
    "column_name": {
      "datatype": "тип данных в PostgreSQL",
      "placeholder": "пример значения",
      "теги": "ключевые слова через запятую",
      "описание": "описание колонки на русском"
    }
  },
  "imported_from": "источник импорта (опционально)",
  "import_date": "дата импорта (опционально)",
  "note": "дополнительные заметки (опционально)"
}
```

### Совместимость с column_descriptions.json
Формат полностью совместим с существующим `column_descriptions.json`:

```json
{
  "bill_date": {
    "datatype": "date",
    "placeholder": "2025-01-01",
    "теги": "чек, дата",
    "описание": "дата чека"
  }
}
```

## Аутентификация

Все endpoints требуют JWT аутентификации:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  "http://localhost:8000/descriptions/all"
```

## Примеры использования

### 1. Создание описания для новой таблицы
```python
sales_description = {
    "description": "Таблица данных о продажах из кассовых систем",
    "columns": {
        "bill_date": {
            "datatype": "date",
            "placeholder": "2025-01-01",
            "теги": "чек, дата, время",
            "описание": "дата и время создания чека"
        },
        "customer_id": {
            "datatype": "character varying",
            "placeholder": "ABC-12345",
            "теги": "покупатель, клиент, ID",
            "описание": "уникальный идентификатор покупателя"
        }
    }
}

await app_database_service.save_table_description(
    "retail_db", "sales", sales_description
)
```

### 2. Обновление существующего описания
```python
# Получаем текущее описание
current = await app_database_service.get_table_description("retail_db", "sales")

# Добавляем новую колонку
current["columns"]["new_column"] = {
    "datatype": "numeric",
    "placeholder": "100.50",
    "теги": "сумма, деньги",
    "описание": "сумма транзакции"
}

# Сохраняем обновленное описание
await app_database_service.save_table_description(
    "retail_db", "sales", current
)
```

### 3. Миграция из column_descriptions.json
```python
from config.settings import DB_SCHEMA_CONTEXT

# Автоматический импорт для всех таблиц в data_database
schema = await data_database_service.get_database_schema()
database_name = data_database_service.get_database_name()

for table_name in schema.keys():
    table_desc = {
        "description": f"Таблица {table_name} (импортировано из column_descriptions.json)",
        "columns": DB_SCHEMA_CONTEXT
    }
    
    await app_database_service.save_table_description(
        database_name, table_name, table_desc
    )
```

## Преимущества

1. **Централизованное хранение**: все описания в одной таблице базы данных
2. **Версионность**: отслеживание даты создания и обновления
3. **Гибкость**: поддержка множественных баз данных и таблиц
4. **Совместимость**: полная совместимость с форматом column_descriptions.json
5. **API-первый подход**: управление через REST API
6. **Автоматическая интеграция**: описания автоматически подключаются к схеме БД
7. **Fallback-механизм**: откат на legacy column_descriptions.json при необходимости

## Мониторинг

Для проверки состояния системы описаний:

```bash
# Проверка подключения к текущей базе данных
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/descriptions/current-data-database"

# Количество сохраненных описаний
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/descriptions/all" | jq '.total_count'
``` 