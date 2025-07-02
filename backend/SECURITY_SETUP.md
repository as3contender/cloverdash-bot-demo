# 🔐 Настройка безопасности CloverdashBot Backend

## Генерация секретного ключа для JWT

### Быстрый старт

```bash
# Генерация ключа
python generate_secret_key.py

# или через make
make secret-key
```

### Что вы получите

Скрипт сгенерирует 3 варианта ключей:

1. **Base64 ключ (рекомендуется)** - 32 байта в base64
2. **Длинный Base64 ключ** - 64 байта для повышенной безопасности  
3. **Алфавитно-цифровой ключ** - 64 символа из букв и цифр

### Настройка .env файла

Скопируйте один из сгенерированных ключей в ваш `.env` файл:

```env
# Замените your-secret-key-here на сгенерированный ключ
SECRET_KEY=rF66tU5rWBkq4KoD70jSNsy956NSSTtkaFzNHPWT_N8=
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200
```

## Параметры безопасности

### Обязательные настройки

| Параметр | Описание | Пример |
|----------|----------|---------|
| `SECRET_KEY` | Секретный ключ для подписи JWT токенов | `rF66tU5r...` |
| `ALGORITHM` | Алгоритм шифрования (рекомендуется HS256) | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Время жизни токена в минутах | `43200` (30 дней) |

### Дополнительные настройки

```env
# CORS настройки
ALLOWED_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]

# Для разработки можно использовать:
ALLOWED_ORIGINS=["*"]
```

## Рекомендации по безопасности

### 🟢 Что делать

1. **Генерируйте уникальные ключи** для каждого окружения
2. **Используйте HTTPS** в продакшене
3. **Ограничьте CORS** для продакшена конкретными доменами
4. **Регулярно обновляйте** секретные ключи
5. **Используйте переменные окружения** для хранения секретов

### 🔴 Чего не делать

1. ❌ **Не коммитьте** `.env` файлы в Git
2. ❌ **Не используйте** одинаковые ключи для разработки и продакшена
3. ❌ **Не делитесь** секретными ключами
4. ❌ **Не используйте** простые или предсказуемые ключи
5. ❌ **Не оставляйте** `ALLOWED_ORIGINS=["*"]` в продакшене

## Разные окружения

### Разработка (.env.development)
```env
SECRET_KEY=dev-key-here-can-be-simpler-but-still-secure
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 1 день
ALLOWED_ORIGINS=["*"]
```

### Продакшен (.env.production)
```env
SECRET_KEY=super-secure-production-key-very-long-and-random
ACCESS_TOKEN_EXPIRE_MINUTES=43200  # 30 дней
ALLOWED_ORIGINS=["https://yourdomain.com"]
```

### Тестирование (.env.test)
```env
SECRET_KEY=test-key-for-testing-environment
ACCESS_TOKEN_EXPIRE_MINUTES=60  # 1 час
ALLOWED_ORIGINS=["*"]
```

## Проверка безопасности

### Тест подключения

```bash
# Запуск сервера
python main.py

# Проверка health endpoint
curl http://localhost:8000/health/

# Тест аутентификации (должен вернуть 401)
curl http://localhost:8000/database/schema
```

### Тест JWT токенов

```python
# Тестовый скрипт
from services.security import security_service

# Создание токена
token = security_service.create_access_token({"sub": "test_user_id"})
print(f"Token: {token}")

# Проверка токена
token_data = security_service.verify_token(token)
print(f"User ID: {token_data.user_id}")
```

## Устранение проблем

### Ошибка "Could not validate credentials"

1. Проверьте правильность `SECRET_KEY` в `.env`
2. Убедитесь, что токен не истек
3. Проверьте формат заголовка: `Authorization: Bearer YOUR_TOKEN`

### Ошибка CORS

1. Добавьте ваш домен в `ALLOWED_ORIGINS`
2. Для разработки используйте `["*"]`
3. Проверьте протокол (http/https)

### Токены не работают после перезапуска

- Это нормально, если вы меняли `SECRET_KEY`
- Все существующие токены становятся недействительными
- Пользователям нужно будет войти заново

## Мониторинг безопасности

### Логи аутентификации

Проверяйте логи на подозрительную активность:

```bash
# Фильтр логов аутентификации
docker logs backend_container | grep "auth"

# Или в файлах логов
tail -f /path/to/logs/app.log | grep "Failed\|Unauthorized"
```

### Метрики

Следите за:
- Количеством неудачных попыток входа
- Использованием просроченных токенов
- Подозрительными IP адресами 