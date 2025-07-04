# 🚀 Deployment Scripts

Скрипты для развертывания CloverdashBot на удаленном сервере.

## 📋 Список скриптов

### Основные скрипты развертывания:
- **`deploy_all.sh`** - Главный скрипт развертывания (backend + telegram-bot)
- **`setup_deploy.sh`** - Интерактивная настройка конфигурации
- **`deploy.env.example`** - Пример конфигурации развертывания

### Управление и мониторинг:
- **`logs.sh`** - Просмотр логов сервисов
- **`analyze_deployment_size.sh`** - Анализ размера развертывания

### Диагностика и исправления:
- **`test_docker_installation.sh`** - Тестирование Docker установки
- **`debug_docker.sh`** - Диагностика Docker проблем
- **`fix_docker_compose.sh`** - Исправление docker-compose
- **`diagnose_backend_failure.sh`** - Диагностика проблем с backend

## 🚀 Быстрый старт

```bash
# 1. Настройте конфигурацию
./setup_deploy.sh

# 2. Проанализируйте размер развертывания (опционально)
./analyze_deployment_size.sh

# 3. Разверните проект
./deploy_all.sh

# 4. Если развертывание не удалось - диагностика
./diagnose_backend_failure.sh
```

## 📊 Оптимизация развертывания

Проект использует многоуровневую оптимизацию для минимизации объема передаваемых данных:

### 🎯 Исключения при копировании на сервер:
- **`.deployignore`** - исключает файлы разработки при передаче на сервер
- Использует `rsync` вместо `scp` для эффективной передачи
- Исключает: документацию, тесты, IDE файлы, кэш Python, виртуальные окружения

### 🐳 Исключения при сборке Docker образов:
- **`backend/.dockerignore`** - оптимизация для backend контейнера
- **`telegram-bot/.dockerignore`** - оптимизация для bot контейнера
- Исключает: утилиты разработки, тестовые файлы, временные файлы

### 📈 Анализ эффективности:
```bash
# Запустите анализ размера
./analyze_deployment_size.sh
```

Показывает:
- Размер без оптимизации vs с оптимизацией
- Процент экономии места
- Количество исключенных файлов
- Преимущества оптимизации

## 🚨 Диагностика проблем

### Backend не запускается?
```bash
# Запустите полную диагностику
./diagnose_backend_failure.sh

# Быстрая проверка логов
./logs.sh backend

# Перезапуск backend
ssh -i ~/.ssh/your-key user@server 'cd /opt/cloverdash-bot/backend && docker-compose restart'
```

### Основные причины ошибок:
1. **Неправильный путь health check** (исправлено в текущей версии)
2. **Проблемы с базой данных** - PostgreSQL не запущен или неправильные credentials
3. **Недоступность OpenAI API** - неправильный или истекший API ключ
4. **Проблемы с Docker** - недостаточно памяти или ошибки сборки
5. **Сетевые проблемы** - порты заблокированы или неправильная конфигурация

## 📖 Подробная документация

См. `DEPLOYMENT_README.md` для:
- Детальные инструкции по настройке
- Примеры использования
- Диагностика проблем
- Команды управления сервисами

## 📁 Структура

```
deployment/
├── deploy_all.sh                 # 🚀 Основной скрипт развертывания
├── test_docker_installation.sh  # 🔍 Диагностика Docker на сервере
├── setup_deploy.sh              # ⚙️ Интерактивный помощник настройки
├── logs.sh                      # 📊 Просмотр логов удаленных сервисов
├── fix_docker_compose.sh        # 🔧 Исправление проблем с docker-compose
├── debug_docker.sh              # 🐛 Диагностика Docker проблем
├── deploy.env.example           # 📄 Пример конфигурации развертывания
├── deploy.env                   # 🔐 Ваша конфигурация (создается автоматически)
├── DEPLOYMENT_README.md         # 📚 Подробная документация
└── README.md                    # 📖 Этот файл
```

## 🚀 Быстрый старт

### 1. Настройка конфигурации:
```bash
cd deployment
# Создать конфигурацию интерактивно
./setup_deploy.sh

# Или скопировать и отредактировать вручную
cp deploy.env.example deploy.env
nano deploy.env
```

### 2. Развертывание:
```bash
# Полное развертывание (Backend + Bot)
./deploy_all.sh

# Только Backend API
./deploy_all.sh --backend-only

# Только Telegram Bot  
./deploy_all.sh --bot-only
```

### 3. Диагностика (опционально):
```bash
# Проверить Docker на сервере перед развертыванием
./test_docker_installation.sh

# Исправить проблемы с docker-compose
./fix_docker_compose.sh
```

## 📊 Управление после развертывания

### Просмотр логов:
```bash
# Backend логи
./logs.sh backend

# Bot логи
./logs.sh bot

# Статус всех сервисов
./logs.sh --status
```

### Полезные опции:
```bash
# Следить за логами в реальном времени
./logs.sh backend -f

# Показать последние 100 строк
./logs.sh bot -n 100
```

## ⚙️ Основные скрипты

| Скрипт | Описание | Использование |
|--------|----------|---------------|
| `deploy_all.sh` | Основной скрипт развертывания всего стека | `./deploy_all.sh [--backend-only\|--bot-only]` |
| `test_docker_installation.sh` | Диагностика Docker установки на сервере | `./test_docker_installation.sh` |
| `setup_deploy.sh` | Интерактивная настройка конфигурации | `./setup_deploy.sh` |
| `logs.sh` | Просмотр логов удаленных сервисов | `./logs.sh [backend\|bot] [-f] [-n NUM]` |
| `fix_docker_compose.sh` | Исправление проблем с docker-compose | `./fix_docker_compose.sh` |
| `debug_docker.sh` | Расширенная диагностика Docker | `./debug_docker.sh` |

## 🔧 Конфигурация

### Обязательные настройки в `deploy.env`:
```env
REMOTE_HOST=64.227.69.138          # IP адрес сервера
REMOTE_USER=root                   # SSH пользователь
SSH_KEY_PATH=~/.ssh/your-key       # Путь к SSH ключу (опционально)
```

### Дополнительные настройки:
```env
DEPLOY_BACKEND=true                # Развертывать Backend API
DEPLOY_BOT=true                    # Развертывать Telegram Bot
REMOTE_DEPLOY_DIR=/opt/cloverdash-bot  # Папка на сервере
```

## 📚 Подробная документация

Полная документация со всеми деталями находится в файле `DEPLOYMENT_README.md`.

## 🎯 Примеры использования

```bash
# Создать конфигурацию
./setup_deploy.sh

# Протестировать Docker
./test_docker_installation.sh

# Развернуть весь стек
./deploy_all.sh

# Посмотреть логи
./logs.sh backend -f

# Развернуть только backend с custom параметрами
./deploy_all.sh --backend-only -h my-server.com -u ubuntu
```

---

**💡 Совет**: Начните с запуска `./setup_deploy.sh` для интерактивной настройки, а затем `./deploy_all.sh` для развертывания. 