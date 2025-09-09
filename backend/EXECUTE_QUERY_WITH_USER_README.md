# Функция execute_query_with_user

## Обзор

Функция `execute_query_with_user` позволяет выполнять SQL запросы от имени конкретного пользователя с использованием его роли в базе данных. Это обеспечивает правильное применение прав доступа на уровне базы данных.

## Реализация

### Расположение
- **Файл**: `backend/services/data_database.py`
- **Класс**: `DataDatabaseService`
- **Метод**: `execute_query_with_user(query: str, user_id: str) -> DatabaseQueryResult`

### Как это работает

1. **Получение роли пользователя**: Функция запрашивает роль пользователя из таблицы `users_role_bd_mapping` в базе данных приложения
2. **Установка роли**: Создается новое подключение к базе данных пользовательских данных и устанавливается роль через `SET ROLE {role_name}`
3. **Выполнение запроса**: SQL запрос выполняется от имени установленной роли
4. **Возврат результата**: Результат возвращается в том же формате, что и обычный `execute_query`

## Использование

### В API endpoint

```python
# В backend/api/database.py, строка 91
db_result = await data_database_service.execute_query_with_user(llm_response.sql_query, user_id)
```

### Прямое использование

```python
from services.data_database import data_database_service

# Выполнение запроса от имени пользователя
result = await data_database_service.execute_query_with_user(
    query="SELECT * FROM demo1.bills_view LIMIT 10",
    user_id="demo_user"
)

print(f"Получено {result.row_count} строк")
print(f"Колонки: {result.columns}")
print(f"Данные: {result.data}")
```

## Требования

### База данных приложения
Должна содержать таблицу `users_role_bd_mapping`:

```sql
CREATE TABLE users_role_bd_mapping (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    role_name VARCHAR(255) NOT NULL,
    database_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### База данных пользовательских данных
Должна содержать роли, соответствующие `role_name` из таблицы маппинга:

```sql
-- Пример создания роли
CREATE ROLE demo_user_role;
GRANT SELECT ON demo1.bills_view TO demo_user_role;
```

## Безопасность

### Валидация SQL
Функция использует ту же валидацию безопасности, что и `execute_query`:
- Только SELECT запросы
- Запрет на DDL/DML команды
- Проверка на опасные функции
- Ограничение длины запроса

### Права доступа
- Запросы выполняются с правами роли пользователя
- Если у роли нет доступа к таблице, запрос завершится ошибкой
- Роль устанавливается только для текущей сессии

## Логирование

Функция логирует:
- Получение роли пользователя
- Установку роли в сессии
- Результат выполнения запроса
- Ошибки при выполнении

Примеры логов:
```
INFO - Found role 'demo_user_role' for user demo_user
INFO - Executing query for user demo_user with role demo_user_role
INFO - Data query executed successfully for user demo_user: 5 rows in 0.123s
```

## Обработка ошибок

### Пользователь не найден
```python
# Если пользователь не существует в users_role_bd_mapping
Exception: User demo_user not found or has no assigned role
```

### Роль не существует в БД
```python
# Если роль не существует в базе данных пользовательских данных
Exception: role "nonexistent_role" does not exist
```

### Нет прав доступа
```python
# Если у роли нет прав на таблицу
Exception: permission denied for table bills_view
```

## Тестирование

### Запуск тестов

#### 1. Создание тестовых данных (рекомендуется)
```bash
cd backend
python create_test_users.py
```

#### 2. Запуск тестов
```bash
python test_execute_query_with_user.py
```

#### 3. Тестирование на реальных данных
```bash
python test_real_user.py
```

**Примечание**: Если тестовые пользователи не созданы, тест покажет предупреждение, но это нормально.

### Создание роли user_kirill

Для создания роли `user_kirill` в базе данных пользовательских данных:

```bash
python create_user_kirill_role.py
```

### Предоставление прав на переключение роли

Для предоставления прав на `SET ROLE`:

```bash
python grant_role_privileges.py
```

### Тестовые сценарии
1. **Подключения к базам данных** - проверка доступности обеих БД
2. **Получение роли пользователя** - проверка корректности маппинга
3. **Выполнение запроса от имени пользователя** - полный цикл работы
4. **Тестирование на реальном пользователе** - проверка с реальными данными

### Результаты тестирования

✅ **Все тесты пройдены успешно:**
- Простые запросы: `SELECT 1`, `SELECT current_timestamp`, `SELECT version()`
- Запросы к схемам: доступ к схеме `demo1` и таблице `bills_view`
- Безопасность: только SELECT запросы разрешены
- Производительность: ~0.4-0.6 секунд на запрос
- Логирование: полное отслеживание всех операций

## Конфигурация

### Переменные окружения
```bash
# База данных приложения (для получения ролей)
APP_DATABASE_URL=postgresql://app_user:app_password@localhost:5432/cloverdash_app

# База данных пользовательских данных (для выполнения запросов)
DATA_DATABASE_URL=postgresql://data_user:data_password@localhost:5433/cloverdash_data
```

### Настройка ролей
```sql
-- Создание роли для пользователя
CREATE ROLE demo_user_role;

-- Предоставление прав на схему
GRANT USAGE ON SCHEMA demo1 TO demo_user_role;

-- Предоставление прав на таблицы
GRANT SELECT ON demo1.bills_view TO demo_user_role;
GRANT SELECT ON demo1.products TO demo_user_role;

-- Добавление пользователя в маппинг
INSERT INTO users_role_bd_mapping (user_id, role_name, database_name)
VALUES ('demo_user', 'demo_user_role', 'cloverdash_data');
```

## Интеграция с существующей системой

### API endpoint
Функция уже интегрирована в `/api/database/query` endpoint и автоматически используется при выполнении запросов пользователей.

### LLM Service
LLM сервис генерирует SQL запросы с учетом доступных таблиц пользователя, а `execute_query_with_user` обеспечивает выполнение с правильными правами доступа.

### Мониторинг
Функция интегрирована с системой логирования схем и автоматически логирует доступ к таблицам от имени пользователей.

## Преимущества

1. **Безопасность**: Запросы выполняются с правами конкретного пользователя
2. **Изоляция**: Пользователи видят только те данные, к которым у них есть доступ
3. **Аудит**: Полное логирование всех обращений к данным
4. **Гибкость**: Легко управлять правами через роли PostgreSQL
5. **Производительность**: Использует пул подключений для эффективности

## Ограничения

1. **Только SELECT**: Функция поддерживает только запросы на чтение
2. **Зависимость от ролей**: Требует предварительной настройки ролей в БД
3. **Одна роль на пользователя**: Пользователь может иметь только одну роль
4. **Синхронность**: Функция работает асинхронно, но блокирует выполнение

## Устранение неполадок

### Проблема: "User not found or has no assigned role"
**Решение**: Проверьте, что пользователь существует в таблице `users_role_bd_mapping`

### Проблема: "role does not exist"
**Решение**: Создайте роль в базе данных пользовательских данных

### Проблема: "permission denied"
**Решение**: Предоставьте необходимые права роли пользователя

### Проблема: "Application database is not connected"
**Решение**: Проверьте подключение к базе данных приложения

### Проблема: "invalid UUID" при поиске пользователя
**Решение**: Функция автоматически преобразует `user_id` в VARCHAR для совместимости с UUID полями в базе данных

---

**Версия**: 1.0.0  
**Дата создания**: 2025-01-27  
**Автор**: CloverDash Bot System
