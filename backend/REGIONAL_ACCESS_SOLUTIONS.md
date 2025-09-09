# Решения для обхода региональных ограничений OpenAI

## Проблема
Ошибка: `403 - unsupported_country_region_territory` означает, что OpenAI заблокировал доступ из вашего региона.

## Решение 1: Использование прокси (рекомендуется)

### Настройка в .env файле:
```bash
# Основные настройки OpenAI
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TEMPERATURE=0

# Прокси настройки
OPENAI_PROXY=http://proxy-server:port
# или для SOCKS прокси:
# OPENAI_PROXY=socks5://proxy-server:port

# Альтернативный базовый URL (если используете прокси-сервис)
# OPENAI_BASE_URL=https://api.openai-proxy.com/v1
```

### Популярные прокси-сервисы для OpenAI:
- **ProxyMesh** - специализируется на API прокси
- **Bright Data** - корпоративные прокси
- **Smartproxy** - API прокси с поддержкой OpenAI
- **Oxylabs** - премиум прокси

## Решение 2: Альтернативные LLM провайдеры

### 2.1 Anthropic Claude
```bash
# В .env файле:
ANTHROPIC_API_KEY=your_anthropic_api_key
ANTHROPIC_MODEL=claude-3-sonnet-20240229
```

### 2.2 Google Gemini
```bash
# В .env файле:
GOOGLE_API_KEY=your_google_api_key
GOOGLE_MODEL=gemini-pro
```

### 2.3 YandexGPT (для России)
```bash
# В .env файле:
YANDEX_API_KEY=your_yandex_api_key
YANDEX_MODEL=yandexgpt
```

## Решение 3: Локальные LLM

### 3.1 Ollama
```bash
# Установка Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Запуск модели
ollama run llama2

# В .env файле:
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

### 3.2 LM Studio
```bash
# Скачать с https://lmstudio.ai/
# В .env файле:
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_MODEL=local-model
```

## Решение 4: Модификация кода для поддержки альтернативных провайдеров

### Пример модификации llm_service.py:

```python
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

class LLMService:
    def __init__(self):
        # Определяем провайдера
        provider = os.getenv("LLM_PROVIDER", "openai")
        
        if provider == "anthropic":
            self.llm = ChatAnthropic(
                model=settings.anthropic_model,
                anthropic_api_key=settings.anthropic_api_key
            )
        elif provider == "google":
            self.llm = ChatGoogleGenerativeAI(
                model=settings.google_model,
                google_api_key=settings.google_api_key
            )
        elif provider == "ollama":
            self.llm = ChatOpenAI(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model,
                api_key="ollama"  # Ollama не требует реального API ключа
            )
        else:  # OpenAI по умолчанию
            self.llm = ChatOpenAI(
                model_name=settings.openai_model,
                temperature=settings.openai_temperature,
                openai_api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                http_client=http_client,
            )
```

## Быстрое решение (временное)

Если нужно быстро запустить проект, можно использовать демо-режим:

```bash
# В .env файле:
OPENAI_API_KEY=demo_key
OPENAI_MODEL=gpt-3.5-turbo
DEMO_MODE=true
```

И модифицировать код для работы в демо-режиме с предустановленными SQL запросами.

## Рекомендации

1. **Начните с прокси** - это самое простое решение
2. **Попробуйте Anthropic Claude** - часто доступен в заблокированных регионах
3. **Рассмотрите локальные LLM** - для полной независимости
4. **Используйте YandexGPT** - если находитесь в России

## Проверка решения

После настройки проверьте подключение:

```bash
cd backend
python -c "
from services.llm_service import llm_service
import asyncio
result = asyncio.run(llm_service.test_connection())
print(f'Connection test: {result}')
"
```
