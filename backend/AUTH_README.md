# Система аутентификации CloverdashBot

## Обзор

Система аутентификации требует JWT токены для всех операций с базой данных. Поддерживает:
1. **Web/API клиенты** - стандартная аутентификация через email/username и пароль
2. **Telegram бот** - аутентификация через Telegram ID с автоматической регистрацией

## Endpoints аутентификации

### 1. Регистрация пользователя
```
POST /auth/register
```

**Тело запроса:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "password": "secure_password",
  "telegram_id": "123456789",
  "telegram_username": "johndoe"
}
```

**Ответ:**
```json
{
  "id": "uuid",
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "telegram_id": "123456789",
  "telegram_username": "johndoe",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

### 2. Вход в систему (OAuth2 Form)
```
POST /auth/login
Content-Type: application/x-www-form-urlencoded
```

**Тело запроса:**
```
username=john@example.com&password=secure_password
```

### 3. Вход в систему (JSON)
```
POST /auth/login/json
```

**Тело запроса:**
```json
{
  "username": "john@example.com",
  "password": "secure_password"
}
```

**Ответ для обоих типов входа:**
```json
{
  "access_token": "jwt_token_here",
  "token_type": "bearer",
  "expires_in": 2592000
}
```

### 4. Telegram аутентификация
```
POST /auth/telegram
```

**Тело запроса:**
```json
{
  "telegram_id": "123456789",
  "telegram_username": "johndoe",
  "first_name": "John",
  "last_name": "Doe"
}
```

### 5. Получение информации о текущем пользователе
```
GET /auth/me
Authorization: Bearer jwt_token_here
```

## Защищенные endpoints

Все следующие endpoints требуют аутентификации:

### База данных:
- `POST /database/query` - выполнение запросов к базе данных
- `GET /database/schema` - получение схемы базы данных  
- `POST /database/sql` - выполнение прямых SQL запросов

### Пример использования:

```bash
# Получение токена
curl -X POST "http://localhost:8000/auth/login/json" \
  -H "Content-Type: application/json" \
  -d '{"username": "john@example.com", "password": "secure_password"}'

# Использование токена для запроса
curl -X POST "http://localhost:8000/database/query" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Покажи всех пользователей"}'
```

## Публичные endpoints

Следующие endpoints доступны без аутентификации:

- `GET /health/` - проверка состояния сервиса
- `GET /health/info` - информация о сервисах
- `GET /` - корневой endpoint с информацией об API

## Настройки аутентификации

В файле `.env`:

```env
# Секретный ключ для подписи JWT токенов (ОБЯЗАТЕЛЬНО изменить в продакшене!)
SECRET_KEY=your-super-secret-key-change-this-in-production

# Алгоритм шифрования
ALGORITHM=HS256

# Время жизни токена в минутах (по умолчанию 30 дней)
ACCESS_TOKEN_EXPIRE_MINUTES=43200
```

## Схема базы данных

Создается таблица `users`:

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE,
    email VARCHAR(255) UNIQUE,
    full_name VARCHAR(255),
    hashed_password VARCHAR(255),
    telegram_id VARCHAR(100) UNIQUE,
    telegram_username VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Типы аутентификации

### 1. Email/Username + Password
Стандартная аутентификация для веб-клиентов и API клиентов.

### 2. Telegram ID
Аутентификация через Telegram ID с автоматической регистрацией пользователя.

## Безопасность

1. **Хэширование паролей** - используется bcrypt
2. **JWT токены** - подписываются секретным ключом
3. **HTTPS** - рекомендуется для продакшена
4. **Ограничения SQL** - только SELECT запросы
5. **Обязательная аутентификация** - нет публичных endpoints для базы данных

## Telegram Bot Integration

Telegram бот автоматически:
1. Аутентифицируется через `/auth/telegram` при первом запросе пользователя
2. Кэширует токены пользователей для повторного использования
3. Обновляет токены при истечении срока действия
4. Использует `/database/query` для всех запросов к базе данных

### Флоу Telegram бота:
```
User Message → Bot authenticates → Bot gets JWT token → Bot queries /database/query → Bot returns result
```

## Примеры интеграции

### Python клиент:
```python
import requests

# Аутентификация
response = requests.post("http://localhost:8000/auth/login/json", json={
    "username": "john@example.com",
    "password": "secure_password"
})
token = response.json()["access_token"]

# Использование токена
headers = {"Authorization": f"Bearer {token}"}
response = requests.post("http://localhost:8000/database/query", 
                        headers=headers,
                        json={"query": "Покажи статистику пользователей"})
```

### JavaScript клиент:
```javascript
// Аутентификация
const authResponse = await fetch('http://localhost:8000/auth/login/json', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        username: 'john@example.com',
        password: 'secure_password'
    })
});
const { access_token } = await authResponse.json();

// Использование токена
const queryResponse = await fetch('http://localhost:8000/database/query', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${access_token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({query: 'Покажи статистику пользователей'})
});
```

### Telegram Bot Integration:
```python
# В боте происходит автоматически:
# 1. Получение токена
auth_response = await session.post(f"{BACKEND_URL}/auth/telegram", json={
    "telegram_id": user_id,
    "telegram_username": username,
    "first_name": first_name,
    "last_name": last_name
})
token = auth_response.json()["access_token"]

# 2. Использование токена для запросов
headers = {"Authorization": f"Bearer {token}"}
query_response = await session.post(f"{BACKEND_URL}/database/query", 
                                   json={"query": user_question},
                                   headers=headers)
```

## Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Client    │    │  Telegram Bot   │    │   API Client    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │ /auth/login/json      │ /auth/telegram        │ /auth/login
         └─────────────────────────────┼─────────────────────────────┘
                                      │
                              ┌───────▼────────┐
                              │  Backend API   │
                              │                │
                              │ ┌─────────────┐│
                              │ │ auth/*      ││
                              │ │ health/*    ││
                              │ │ database/*  ││
                              │ └─────────────┘│
                              └────────────────┘
                                      │
                              ┌───────▼────────┐
                              │   Database     │
                              └────────────────┘
``` 