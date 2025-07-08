.PHONY: help build up down logs clean restart shell test

# Переменные
COMPOSE_FILE = docker-compose.yml
SERVICE_BACKEND = backend

# Помощь
help:
	@echo "Доступные команды для Backend:"
	@echo ""
	@echo "  build        - Собрать образ backend"
	@echo "  up           - Запустить backend"
	@echo "  down         - Остановить backend"
	@echo "  logs         - Показать логи backend"
	@echo "  restart      - Перезапустить backend"
	@echo "  clean        - Остановить и удалить контейнер"
	@echo "  shell        - Войти в контейнер backend"
	@echo "  test         - Запустить тесты в контейнере"
	@echo "  status       - Показать статус сервиса"
	@echo "  secret-key   - Сгенерировать секретный ключ для JWT"

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

# Полная пересборка и запуск
rebuild:
	docker-compose -f $(COMPOSE_FILE) down
	docker-compose -f $(COMPOSE_FILE) build --no-cache
	docker-compose -f $(COMPOSE_FILE) up -d

# Генерация секретного ключа
secret-key:
	python generate_secret_key.py 