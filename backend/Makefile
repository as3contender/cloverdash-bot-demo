# Makefile для CloverdashBot Backend

.PHONY: test test-unit test-integration test-database test-llm test-api test-coverage
.PHONY: install dev-install run clean lint format
.PHONY: help

# По умолчанию показываем помощь
.DEFAULT_GOAL := help

# Цвета для вывода
GREEN=\033[0;32m
YELLOW=\033[1;33m
RED=\033[0;31m
NC=\033[0m # No Color

help: ## Показать это сообщение с помощью
	@echo "$(GREEN)CloverdashBot Backend - Доступные команды:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Установить зависимости
	@echo "$(GREEN)Установка зависимостей...$(NC)"
	pip install -r requirements.txt

dev-install: install ## Установить зависимости для разработки
	@echo "$(GREEN)Установка dev зависимостей...$(NC)"
	pip install -e .

test: ## Запустить все тесты
	@echo "$(GREEN)Запуск всех тестов...$(NC)"
	python -m pytest -v --tb=short

test-unit: ## Запустить только unit тесты
	@echo "$(GREEN)Запуск unit тестов...$(NC)"
	python -m pytest -v -m unit --tb=short

test-integration: ## Запустить только integration тесты
	@echo "$(GREEN)Запуск integration тестов...$(NC)"
	python -m pytest -v -m integration --tb=short

test-database: ## Запустить только database тесты
	@echo "$(GREEN)Запуск database тестов...$(NC)"
	python -m pytest -v -m database --tb=short

test-llm: ## Запустить только LLM тесты
	@echo "$(GREEN)Запуск LLM тестов...$(NC)"
	python -m pytest -v -m llm --tb=short

test-api: ## Запустить только API тесты
	@echo "$(GREEN)Запуск API тестов...$(NC)"
	python -m pytest -v -m api --tb=short

test-coverage: ## Запустить тесты с отчетом о покрытии
	@echo "$(GREEN)Запуск тестов с coverage...$(NC)"
	python -m pytest --cov=. --cov-report=html --cov-report=term-missing --cov-fail-under=80

test-watch: ## Запустить тесты в режиме watch (требует pytest-watch)
	@echo "$(GREEN)Запуск тестов в watch режиме...$(NC)"
	ptw -- --tb=short -v

run: ## Запустить сервер для разработки
	@echo "$(GREEN)Запуск сервера...$(NC)"
	python main.py

run-prod: ## Запустить сервер для продакшена
	@echo "$(GREEN)Запуск production сервера...$(NC)"
	uvicorn main:app --host 0.0.0.0 --port 8000

lint: ## Проверить код линтером
	@echo "$(GREEN)Запуск линтера...$(NC)"
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

format: ## Форматировать код
	@echo "$(GREEN)Форматирование кода...$(NC)"
	black . --line-length 100
	isort . --profile black

clean: ## Очистить временные файлы
	@echo "$(GREEN)Очистка временных файлов...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/

check-env: ## Проверить переменные окружения
	@echo "$(GREEN)Проверка переменных окружения...$(NC)"
	@python -c "from config.settings import settings; print('✅ Конфигурация загружена успешно')" || \
		echo "$(RED)❌ Ошибка загрузки конфигурации$(NC)"

docs: ## Генерировать документацию API
	@echo "$(GREEN)Генерация документации...$(NC)"
	python -c "from main import app; import json; print(json.dumps(app.openapi(), indent=2))" > openapi.json

# Быстрые команды для запуска определенных тестов
t-db: test-database ## Краткий алиас для test-database
t-llm: test-llm ## Краткий алиас для test-llm  
t-api: test-api ## Краткий алиас для test-api
t-unit: test-unit ## Краткий алиас для test-unit
t-int: test-integration ## Краткий алиас для test-integration
t-cov: test-coverage ## Краткий алиас для test-coverage

# Команды для CI/CD
ci-test: ## Команды для CI/CD
	@echo "$(GREEN)CI: Запуск тестов...$(NC)"
	python -m pytest --cov=. --cov-report=xml --cov-report=term --tb=short

ci-lint: ## CI: Проверка линтером
	@echo "$(GREEN)CI: Проверка линтером...$(NC)"
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics 