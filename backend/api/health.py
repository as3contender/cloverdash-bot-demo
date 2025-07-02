from fastapi import APIRouter
from typing import Dict, Any
import logging

from services.app_database import app_database_service
from services.data_database import data_database_service
from services.llm_service import llm_service
from models.base import HealthResponse

logger = logging.getLogger(__name__)

# Создаем роутер для health endpoints
health_router = APIRouter(prefix="/health", tags=["Health"])


@health_router.get("/", response_model=HealthResponse)
async def health_check():
    """Проверка состояния сервисов"""
    try:
        # Проверяем состояние базы данных приложения
        app_db_status = await app_database_service.test_connection() if app_database_service.is_connected else False

        # Проверяем состояние базы данных пользовательских данных
        data_db_status = await data_database_service.test_connection() if data_database_service.is_connected else False

        # Проверяем состояние LLM сервиса
        llm_status = await llm_service.test_connection()

        # Считаем общий статус здоровым, если все сервисы работают
        overall_db_status = app_db_status and data_db_status
        overall_status = "healthy" if overall_db_status and llm_status else "unhealthy"

        return HealthResponse(
            status=overall_status,
            database_connected=overall_db_status,
            llm_service_available=llm_status,
            timestamp=None,  # Pydantic автоматически установит текущее время
        )

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(status="unhealthy", database_connected=False, llm_service_available=False, timestamp=None)


@health_router.get("/info", response_model=Dict[str, Any])
async def get_service_info():
    """
    Возвращает информацию о сервисах (публичный endpoint)

    Returns:
        Dict: Информация о сервисах
    """
    return {
        "databases": {
            "application_db": {
                "connected": app_database_service.is_connected,
                "service": "Application Database Service",
                "description": "Пользователи, история, настройки",
            },
            "data_db": {
                "connected": data_database_service.is_connected,
                "service": "Data Database Service",
                "description": "Пользовательские данные для запросов",
            },
        },
        "llm": llm_service.get_service_info(),
    }
