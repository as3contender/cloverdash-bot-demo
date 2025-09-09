#!/usr/bin/env python3
"""
Демо-версия backend без базы данных для тестирования
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn
from contextlib import asynccontextmanager
from typing import Dict, Any

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения (демо-версия)
    """
    try:
        logger.info("🚀 Starting CloverdashBot Demo Backend...")
        logger.info("📊 Demo mode: No database connection required")
        logger.info("✅ Application startup completed successfully")
        yield
    except Exception as e:
        logger.error(f"❌ Failed to initialize application: {e}")
        raise
    finally:
        logger.info("🔄 Shutting down application...")


# Создаем FastAPI приложение
app = FastAPI(
    title="CloverdashBot Backend (Demo)",
    version="1.0.0",
    description="Демо-версия backend для тестирования функциональности",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=Dict[str, Any])
async def root():
    """Корневой endpoint"""
    return {
        "message": "CloverdashBot Backend (Demo Mode)",
        "version": "1.0.0",
        "status": "running",
        "mode": "demo",
        "database": "not_connected",
        "endpoints": {
            "health": "/health",
            "query": "/query",
            "tables": "/tables",
            "demo": "/demo"
        },
    }


@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Проверка состояния сервиса"""
    return {
        "status": "healthy",
        "message": "CloverdashBot Backend is running in demo mode",
        "database": "demo_mode",
        "timestamp": "2025-09-02T12:00:00Z"
    }


@app.post("/query", response_model=Dict[str, Any])
async def process_query(query_data: Dict[str, Any]):
    """Обработка запроса пользователя (демо-версия)"""
    question = query_data.get("question", "")
    user_id = query_data.get("user_id", "demo_user")
    
    logger.info(f"📝 Demo query from user {user_id}: {question}")
    
    # Демо-ответ
    demo_response = {
        "answer": f"Демо-ответ на вопрос: '{question}'\n\n"
                 f"В реальной версии здесь был бы:\n"
                 f"• SQL запрос, сгенерированный LLM\n"
                 f"• Результаты из базы данных\n"
                 f"• Анализ с учетом прав пользователя {user_id}\n\n"
                 f"Система прав пользователей реализована и готова к работе!",
        "sql_query": f"SELECT * FROM demo_table WHERE question = '{question}'",
        "success": True,
        "execution_time": 0.1,
        "user_id": user_id,
        "mode": "demo"
    }
    
    return demo_response


@app.get("/tables", response_model=Dict[str, Any])
async def get_tables():
    """Получение списка доступных таблиц (демо-версия)"""
    demo_tables = {
        "tables": [
            {
                "name": "users",
                "description": "Таблица пользователей",
                "columns": ["id", "username", "email", "created_at"],
                "accessible": True
            },
            {
                "name": "user_permissions", 
                "description": "Права доступа пользователей",
                "columns": ["id", "role_name", "table_name", "permission_type"],
                "accessible": True
            },
            {
                "name": "database_descriptions",
                "description": "Описания таблиц базы данных", 
                "columns": ["id", "table_name", "description", "columns"],
                "accessible": True
            }
        ],
        "total": 3,
        "mode": "demo"
    }
    
    return demo_tables


@app.get("/demo", response_model=Dict[str, Any])
async def demo_info():
    """Информация о демо-режиме"""
    return {
        "message": "CloverdashBot Demo Mode",
        "features": [
            "✅ Telegram Bot работает",
            "✅ Backend API отвечает", 
            "✅ Система прав реализована",
            "✅ LLM интеграция готова",
            "⏳ База данных: требует подключения"
        ],
        "next_steps": [
            "1. Подключить PostgreSQL",
            "2. Импортировать данные",
            "3. Настроить OpenAI API ключ",
            "4. Полная функциональность готова!"
        ],
        "status": "ready_for_production"
    }


if __name__ == "__main__":
    print("🚀 Запуск CloverdashBot Demo Backend...")
    print("📊 Режим: Демо (без базы данных)")
    print("🌐 URL: http://localhost:8000")
    print("📚 Документация: http://localhost:8000/docs")
    print("✅ Готов к работе!")
    
    uvicorn.run(
        "main_demo:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

