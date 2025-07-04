# 🚀 Deployment Scripts

Папка содержит все скрипты и конфигурации для развертывания CloverdashBot на удаленном сервере.

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