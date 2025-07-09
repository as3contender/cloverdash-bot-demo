# Локальная разработка Backend

## Быстрый старт

### 1. Подготовка окружения

Убедитесь, что у вас установлены:
- Docker и Docker Compose
- PostgreSQL (запущен отдельно)
- Переменные окружения в файле `.env`

### 2. Запуск для локальной разработки

```bash
# Собрать образ
make local-build

# Запустить сервис
make local-up

# Проверить статус
make local-status

# Посмотреть логи
make local-logs
```

### 3. Остановка

```bash
# Остановить сервис
make local-down

# Полная очистка
make local-clean
```

## Отличия от Production

### Локальная версия (`docker-compose.local.yml`):
- ✅ **Hot reload** - код монтируется в контейнер
- ✅ **DEBUG логи** - более подробная информация
- ✅ **Автоматическая сеть** - не требует внешней сети
- ✅ **Интерактивный режим** - stdin_open и tty включены

### Production версия (`docker-compose.yml`):
- 🚀 **Оптимизирована** для production
- 🛡️ **Безопасность** - код не монтируется
- 🌐 **Внешняя сеть** - для связи с другими сервисами
- 📊 **INFO логи** - оптимальный уровень логирования

## Полезные команды

```bash
# Войти в контейнер для отладки
make local-shell

# Перезапустить сервис
make local-restart

# Полная пересборка (при изменении зависимостей)
make local-rebuild

# Запустить тесты
make test
```

## Troubleshooting

### Ошибка "network cloverdash-network declared as external, but could not be found"
Эта ошибка возникает при использовании production docker-compose.yml. Для локальной разработки используйте:
```bash
make local-up  # Вместо make up
```

### Hot reload не работает
Убедитесь, что в `docker-compose.local.yml` раскомментирована строка:
```yaml
volumes:
  - .:/app  # Монтируем код для hot reload
```

### Проблемы с правами доступа
```bash
# Дать права на папку
sudo chown -R $USER:$USER .

# Или запустить с правами пользователя
docker-compose -f docker-compose.local.yml up -d --user $(id -u):$(id -g)
```

## Проверка работы

После запуска проверьте:
1. **Health check**: http://localhost:8000/health
2. **API документация**: http://localhost:8000/docs
3. **Логи**: `make local-logs`

## Переключение между режимами

```bash
# Остановить локальную версию
make local-down

# Запустить production версию
make up

# Или наоборот
make down
make local-up
```

## Структура файлов

```
backend/
├── docker-compose.yml          # Production конфигурация
├── docker-compose.local.yml    # Локальная разработка
├── Makefile                    # Команды для обоих режимов
├── LOCAL_DEVELOPMENT.md        # Эта документация
└── ...
```

## Переменные окружения

Для локальной разработки используйте файл `.env` с настройками:

```bash
# Database
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=your_user
DATABASE_PASSWORD=your_password
DATABASE_NAME=your_database

# OpenAI
OPENAI_API_KEY=your_openai_api_key
```

## Отладка

### Просмотр логов в реальном времени
```bash
make local-logs
```

### Вход в контейнер
```bash
make local-shell
```

### Проверка статуса
```bash
make local-status
```

### Перезапуск приложения
```bash
make local-restart
``` 