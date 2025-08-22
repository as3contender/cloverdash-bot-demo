# Техническое задание: Система разграничения доступа к базам данных

## 📋 Описание проблемы

Необходимо реализовать систему разграничения доступа к таблицам базы данных для различных пользователей компании через cloverdash-bot. Каждый пользователь должен иметь доступ только к определенным таблицам в определенных базах данных.

## 🎯 Цель

Создать систему управления правами доступа, которая:
- Создает индивидуальные роли в базах данных для каждого пользователя
- Предоставляет доступ только на SELECT операции к разрешенным таблицам
- Интегрируется с существующей Admin Panel для управления правами
- Автоматически пересоздает роли при изменении прав доступа

## 🏗️ Архитектура решения

### 1. Новая таблица для маппинга ролей
```sql
CREATE TABLE users_role_bd_mapping (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    database_name VARCHAR(255) NOT NULL,
    schema_name VARCHAR(255) NOT NULL DEFAULT 'public',
    role_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, database_name, schema_name)
);
```

### 2. Расширение таблицы user_permissions
```sql
-- Добавить новые поля в существующую таблицу user_permissions
ALTER TABLE user_permissions ADD COLUMN database_name VARCHAR(255);
ALTER TABLE user_permissions ADD COLUMN schema_name VARCHAR(255) DEFAULT 'public';
ALTER TABLE user_permissions ADD COLUMN table_name VARCHAR(255);
ALTER TABLE user_permissions ADD COLUMN permission_type VARCHAR(50) DEFAULT 'SELECT';
```

## 🔧 Технические требования

### 1. Сервис управления ролями
Создать новый сервис `RoleManagementService` в `backend/services/role_management.py`:

```python
class RoleManagementService:
    async def create_user_role(self, user_id: str, database_name: str, schema_name: str = 'public') -> str
    async def grant_table_permission(self, role_name: str, database_name: str, schema_name: str, table_name: str) -> bool
    async def revoke_table_permission(self, role_name: str, database_name: str, schema_name: str, table_name: str) -> bool
    async def recreate_user_role(self, user_id: str, database_name: str, schema_name: str = 'public') -> bool
    async def delete_user_role(self, user_id: str, database_name: str, schema_name: str = 'public') -> bool
    async def get_user_role_name(self, user_id: str, database_name: str, schema_name: str = 'public') -> Optional[str]
```

### 2. Генерация уникальных имен ролей
```python
def generate_role_name(user_id: str, database_name: str, schema_name: str = 'public') -> str:
    """
    Генерирует уникальное имя роли в формате:
    cloverdash_user_{user_id_hash}_{database_hash}_{schema_hash}_{random_suffix}
    """
    pass
```

### 3. Интеграция с Admin Panel
Расширить Admin Panel для управления правами доступа:
- Добавить вкладку "Управление правами доступа"
- Интерфейс для назначения/отзыва прав на таблицы
- Отображение текущих прав пользователей
- Логирование изменений прав доступа

### 4. API endpoints
Создать новые API endpoints в `backend/api/routes.py`:

```python
# Управление правами доступа
@router.post("/users/{user_id}/permissions")
@router.get("/users/{user_id}/permissions")
@router.put("/users/{user_id}/permissions")
@router.delete("/users/{user_id}/permissions")

# Управление ролями
@router.post("/users/{user_id}/roles")
@router.get("/users/{user_id}/roles")
@router.delete("/users/{user_id}/roles")
```

## 📝 Алгоритм работы

### Сценарий 1: Первое назначение прав пользователю
1. Пользователю `user_1` назначаются права на таблицу `database1.schema1.table_1`
2. Система проверяет существование роли для `user_1` в `database1.schema1`
3. Если роль не существует:
   - Генерируется уникальное имя роли (например: `cloverdash_user_abc123_def456_ghi789_xyz`)
   - Создается роль в базе данных `database1` под админской учеткой
   - Создается запись в `users_role_bd_mapping`
4. Создается запись в `user_permissions`
5. Роли выдаются права на SELECT из таблицы `database1.schema1.table_1`

### Сценарий 2: Добавление дополнительных прав
1. Пользователю `user_1` добавляются права на таблицу `database1.schema1.table_2`
2. Система находит существующую роль в `users_role_bd_mapping`
3. Создается запись в `user_permissions`
4. Роли выдаются права на SELECT из таблицы `database1.schema1.table_2`

### Сценарий 3: Изменение прав доступа
1. Администратор изменяет права пользователя через Admin Panel
2. Система удаляет старую роль из базы данных
3. Создается новая роль с обновленными правами
4. Обновляется запись в `users_role_bd_mapping`
5. Обновляются записи в `user_permissions`

## 🛠️ Требования к реализации

### 1. Безопасность
- Все SQL операции должны использовать параметризованные запросы
- Проверка прав доступа на уровне API
- Логирование всех операций с правами доступа
- Валидация входных данных

### 2. Обработка ошибок
- Обработка ошибок подключения к базам данных
- Rollback транзакций при ошибках
- Информативные сообщения об ошибках
- Graceful degradation при недоступности сервисов

### 3. Производительность
- Кэширование информации о ролях
- Батчевые операции для массовых изменений
- Индексы на часто используемые поля

### 4. Тестирование
- Unit тесты для всех методов сервиса
- Integration тесты для API endpoints
- Тесты на граничные случаи
- Тесты производительности

## 📋 Чек-лист задач

### Этап 1: Базовая инфраструктура
- [ ] Создать миграцию для таблицы `users_role_bd_mapping`
- [ ] Расширить таблицу `user_permissions` новыми полями
- [ ] Создать модель Pydantic для `UserRoleMapping`
- [ ] Создать базовый сервис `RoleManagementService`

### Этап 2: Основная логика
- [ ] Реализовать генерацию уникальных имен ролей
- [ ] Реализовать создание/удаление ролей в базах данных
- [ ] Реализовать выдачу/отзыв прав на таблицы
- [ ] Реализовать пересоздание ролей при изменении прав

### Этап 3: API и интеграция
- [ ] Создать API endpoints для управления правами
- [ ] Интегрировать с существующей системой аутентификации
- [ ] Добавить валидацию и обработку ошибок
- [ ] Создать middleware для проверки прав доступа

### Этап 4: Admin Panel
- [ ] Добавить вкладку управления правами в Admin Panel
- [ ] Создать интерфейс для назначения прав на таблицы
- [ ] Добавить отображение текущих прав пользователей
- [ ] Реализовать логирование изменений

### Этап 5: Тестирование и документация
- [ ] Написать unit тесты
- [ ] Написать integration тесты
- [ ] Создать документацию по API
- [ ] Создать руководство пользователя

## 🔍 Примеры использования

### Пример 1: Назначение прав через API
```python
# Назначить пользователю права на таблицу
response = await client.post(
    f"/api/users/{user_id}/permissions",
    json={
        "database_name": "company_db",
        "schema_name": "public", 
        "table_name": "employees",
        "permission_type": "SELECT"
    }
)
```

### Пример 2: Получение прав пользователя
```python
# Получить все права пользователя
response = await client.get(f"/api/users/{user_id}/permissions")
permissions = response.json()
```

### Пример 3: Удаление прав
```python
# Удалить права на конкретную таблицу
response = await client.delete(
    f"/api/users/{user_id}/permissions",
    params={
        "database_name": "company_db",
        "schema_name": "public",
        "table_name": "employees"
    }
)
```

## ⚠️ Важные замечания

1. **Безопасность**: Все операции с ролями должны выполняться под админской учеткой приложения
2. **Производительность**: При большом количестве пользователей может потребоваться оптимизация
3. **Мониторинг**: Необходимо отслеживать количество созданных ролей и их использование
4. **Резервное копирование**: Регулярно создавать бэкапы таблиц с правами доступа
5. **Документация**: Поддерживать актуальную документацию по правам доступа

## 🎯 Критерии приемки

- [ ] Система корректно создает роли в базах данных
- [ ] Права доступа корректно применяются и отзываются
- [ ] Admin Panel позволяет управлять правами пользователей
- [ ] API endpoints работают корректно и безопасно
- [ ] Все операции логируются
- [ ] Система обрабатывает ошибки gracefully
- [ ] Написаны тесты с покрытием >80%
- [ ] Создана документация по использованию

## 📚 Дополнительные ресурсы

- [Документация PostgreSQL по ролям](https://www.postgresql.org/docs/current/user-manag.html)
- [Документация по SQLAlchemy](https://docs.sqlalchemy.org/)
- [Документация FastAPI](https://fastapi.tiangolo.com/)
- [Документация Streamlit](https://docs.streamlit.io/)
