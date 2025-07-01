# CloverdashBot Demo

Проект состоит из двух основных компонентов:
- **Backend API** (FastAPI) - обработка запросов и анализ данных
- **Telegram Bot** - интерфейс для пользователей через Telegram

## Быстрый старт

### Предварительные требования

1. Docker и Docker Compose
2. PostgreSQL (запущен отдельно)
3. Токен Telegram Bot от @BotFather
4. API ключ OpenAI

### Настройка переменных окружения

1. **Backend** (`backend/.env`):
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

2. **Telegram Bot** (`telegram-bot/.env`):
```bash
TELEGRAM_TOKEN=your_telegram_bot_token
BACKEND_URL=http://localhost:8000
```

### Запуск сервисов

#### 1. Запуск Backend
```bash
cd backend
make build
make up
```

#### 2. Запуск Telegram Bot
```bash
cd telegram-bot
make build  
make up
```

### Управление сервисами

#### Backend команды (из папки `backend/`)
```bash
make help      # Показать все команды
make build     # Собрать образ
make up        # Запустить сервис
make down      # Остановить сервис
make logs      # Показать логи
make restart   # Перезапустить
make status    # Статус сервиса
make shell     # Войти в контейнер
make test      # Запустить тесты
```

#### Telegram Bot команды (из папки `telegram-bot/`)
```bash
make help      # Показать все команды
make build     # Собрать образ
make up        # Запустить бота
make down      # Остановить бота
make logs      # Показать логи
make restart   # Перезапустить
make status    # Статус сервиса
make shell     # Войти в контейнер
```

## Структура проекта

```
cloverdash-bot-demo/
├── backend/
│   ├── docker-compose.yml    # Docker Compose для backend
│   ├── Makefile             # Команды управления backend
│   ├── Dockerfile           # Docker образ backend
│   ├── .env                 # Переменные окружения backend
│   └── ...                  # Остальные файлы backend
│
├── telegram-bot/
│   ├── docker-compose.yml   # Docker Compose для telegram-bot
│   ├── Makefile            # Команды управления bot
│   ├── Dockerfile          # Docker образ bot
│   ├── .env                # Переменные окружения bot
│   └── ...                 # Остальные файлы bot
│
└── README.md               # Этот файл
```

## Порядок запуска

1. **PostgreSQL** - должен быть запущен отдельно
2. **Backend** - запустить первым (`cd backend && make up`)
3. **Telegram Bot** - запустить после backend (`cd telegram-bot && make up`)

## Проверка работы

1. **Backend**: http://localhost:8000/docs
2. **Telegram Bot**: найти бота в Telegram и отправить `/start`

## Troubleshooting

### Конфликты контейнеров
```bash
# Остановить все старые контейнеры
docker ps -a | grep cloverdash
docker rm -f <container_name>
```

### Проблемы с подключением
1. Убедитесь, что PostgreSQL доступен
2. Проверьте переменные окружения в `.env` файлах
3. Убедитесь, что backend запущен перед запуском telegram-bot

### Логи
```bash
# Backend логи
cd backend && make logs

# Telegram Bot логи  
cd telegram-bot && make logs
```

## Описание

Проект состоит из двух основных компонентов:

1. **Telegram Bot** (`telegram-bot/`) - интерфейс для взаимодействия с пользователями
2. **FastAPI Backend** (`backend/`) - API для обработки запросов и работы с LLM

### Функциональность

- 📝 Обработка вопросов на естественном языке
- 🔍 Автоматическое построение SQL запросов с помощью OpenAI
- 🛡️ Безопасность: только SELECT запросы
- 📊 Возможность расширения для отрисовки графиков
- 👥 Планируемая система ролей и ограничений доступа

## Разработка

### Структура проекта

```
cloverdash-bot-demo/
├── backend/
│   ├── main.py              # FastAPI приложение
│   ├── requirements.txt     # Зависимости backend
│   └── .env                 # Конфигурация (не в git)
├── telegram-bot/
│   ├── bot.py              # Telegram bot
│   ├── requirements.txt    # Зависимости bot
│   └── .env                # Конфигурация (не в git)
├── description.txt         # Описание проекта
├── plan.txt               # План разработки
└── README.md              # Документация
```

### API Endpoints

#### Backend API

- `GET /` - Информация о API
- `GET /health` - Проверка состояния
- `POST /query` - Обработка запроса пользователя

#### Пример запроса:
```json
{
  "question": "Сколько заказов было за последний месяц?",
  "user_id": "123456789"
}
```

#### Пример ответа:
```json
{
  "answer": "За последний месяц было сделано 1,245 заказов",
  "sql_query": "SELECT COUNT(*) FROM orders WHERE created_at >= NOW() - INTERVAL '1 month'",
  "success": true
}
```

## TODO

- [ ] Настройка подключения к демо базе данных
- [ ] Создание пользователя с правами только SELECT
- [ ] Создание таблицы с описаниями колонок витрины
- [ ] Отрисовка графиков
- [ ] Система ролей и ограничений доступа
- [ ] Обработка ошибок и валидация запросов
- [ ] Кэширование результатов
- [ ] Логирование и мониторинг

## Вклад в проект

1. Fork проекта
2. Создайте feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit ваши изменения (`git commit -m 'Add some AmazingFeature'`)
4. Push в branch (`git push origin feature/AmazingFeature`)
5. Создайте Pull Request

## Лицензия

Этот проект является демонстрационным. 