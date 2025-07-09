.PHONY: help build up down logs clean restart shell test local-build local-up local-down local-logs local-shell

# Переменные
COMPOSE_FILE = docker-compose.yml
COMPOSE_LOCAL_FILE = docker-compose.local.yml
SERVICE_BACKEND = backend

# Помощь
help:
	@echo "Доступные команды для Backend:"
	@echo ""
	@echo "=== Production команды ==="
	@echo "  build        - Собрать образ backend (production)"
	@echo "  up           - Запустить backend (production)"
	@echo "  down         - Остановить backend (production)"
	@echo "  logs         - Показать логи backend (production)"
	@echo "  restart      - Перезапустить backend (production)"
	@echo "  clean        - Остановить и удалить контейнер (production)"
	@echo "  shell        - Войти в контейнер backend (production)"
	@echo "  test         - Запустить тесты в контейнере"
	@echo "  status       - Показать статус сервиса"
	@echo "  secret-key   - Сгенерировать секретный ключ для JWT"
	@echo ""
	@echo "=== Local Development команды ==="
	@echo "  local-build  - Собрать образ backend (local development)"
	@echo "  local-up     - Запустить backend (local development)"
	@echo "  local-down   - Остановить backend (local development)"
	@echo "  local-logs   - Показать логи backend (local development)"
	@echo "  local-shell  - Войти в контейнер backend (local development)"
	@echo "  local-rebuild- Полная пересборка для локальной разработки"

# Команды для управления
build:
	docker-compose -f $(COMPOSE_FILE) build

up:
	docker-compose -f $(COMPOSE_FILE) up -d

down:
	docker-compose -f $(COMPOSE_FILE) down

logs:
	docker-compose -f $(COMPOSE_FILE) logs -f

restart:
	docker-compose -f $(COMPOSE_FILE) restart

clean:
	docker-compose -f $(COMPOSE_FILE) down
	docker system prune -f

shell:
	docker-compose -f $(COMPOSE_FILE) exec $(SERVICE_BACKEND) bash

test:
	docker-compose -f $(COMPOSE_FILE) exec $(SERVICE_BACKEND) python -m pytest

status:
	docker-compose -f $(COMPOSE_FILE) ps

# Полная пересборка и запуск (production)
rebuild:
	docker-compose -f $(COMPOSE_FILE) down
	docker-compose -f $(COMPOSE_FILE) build --no-cache
	docker-compose -f $(COMPOSE_FILE) up -d

# === Local Development команды ===
local-build:
	docker-compose -f $(COMPOSE_LOCAL_FILE) build

local-up:
	docker-compose -f $(COMPOSE_LOCAL_FILE) up -d

local-down:
	docker-compose -f $(COMPOSE_LOCAL_FILE) down

local-logs:
	docker-compose -f $(COMPOSE_LOCAL_FILE) logs -f

local-shell:
	docker-compose -f $(COMPOSE_LOCAL_FILE) exec $(SERVICE_BACKEND) bash

local-restart:
	docker-compose -f $(COMPOSE_LOCAL_FILE) restart

local-status:
	docker-compose -f $(COMPOSE_LOCAL_FILE) ps

local-clean:
	docker-compose -f $(COMPOSE_LOCAL_FILE) down
	docker system prune -f

# Полная пересборка для локальной разработки
local-rebuild:
	docker-compose -f $(COMPOSE_LOCAL_FILE) down
	docker-compose -f $(COMPOSE_LOCAL_FILE) build --no-cache
	docker-compose -f $(COMPOSE_LOCAL_FILE) up -d

# Генерация секретного ключа
secret-key:
	python generate_secret_key.py 