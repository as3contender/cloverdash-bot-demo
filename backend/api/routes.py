from fastapi import APIRouter
from typing import Dict, Any

from api.auth import auth_router
from api.health import health_router
from api.database import database_router
from api.table_descriptions import descriptions_router

# Создаем главный роутер
router = APIRouter()

# Включаем все модульные роуты
router.include_router(auth_router)
router.include_router(health_router)
router.include_router(database_router)
router.include_router(descriptions_router)


@router.get("/", response_model=Dict[str, Any])
async def root():
    """Корневой endpoint"""
    return {
        "message": "CloverdashBot Backend API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "auth": "/auth/*",
            "health": "/health/*",
            "database": "/database/*",
            "descriptions": "/descriptions/*",
        },
    }
