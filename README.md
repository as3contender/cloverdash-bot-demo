# CloverdashBot Demo

Телеграм-бот с FastAPI backend'ом для работы с базой данных через естественный язык с использованием LLM (OpenAI).

## Архитектура

```
[Telegram Bot] <---> [FastAPI Backend] <---> [DB + Langchain/OpenAI]
                                      |
                        [Контекстная схема БД]
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

## Быстрый старт

### Предварительные требования

- Python 3.8+
- PostgreSQL (или другая SQL база данных)
- OpenAI API ключ
- Telegram Bot Token

### Установка

1. **Клонируйте репозиторий:**
```bash
git clone <repository-url>
cd cloverdash-bot-demo
```

2. **Настройка Backend:**
```bash
cd backend
pip install -r requirements.txt
```

3. **Настройка Telegram Bot:**
```bash
cd ../telegram-bot
pip install -r requirements.txt
```

### Конфигурация

1. **Backend конфигурация:**
Создайте файл `backend/.env`:
```env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
API_HOST=0.0.0.0
API_PORT=8000
```

2. **Telegram Bot конфигурация:**
Создайте файл `telegram-bot/.env`:
```env
TELEGRAM_TOKEN=your_telegram_bot_token_here
BACKEND_URL=http://localhost:8000
```

### Запуск

1. **Запуск Backend:**
```bash
cd backend
python main.py
```

2. **Запуск Telegram Bot:**
```bash
cd telegram-bot
python bot.py
```

## Использование

1. Найдите вашего бота в Telegram
2. Отправьте команду `/start`
3. Задавайте вопросы о данных на естественном языке

### Примеры вопросов:

- "Покажи топ-10 клиентов по объему продаж"
- "Сколько новых пользователей зарегистрировалось на этой неделе?"
- "Какой средний чек в разрезе по регионам?"

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