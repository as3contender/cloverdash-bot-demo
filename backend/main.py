from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn
from contextlib import asynccontextmanager

from config.settings import settings
from services.app_database import app_database_service
from services.data_database import data_database_service
from services.user_service import user_service
from api.routes import router


# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения
    """
    try:
        # Инициализация базы данных приложения (пользователи, история, настройки)
        logger.info("Initializing application database...")
        await app_database_service.initialize()

        # Создание таблиц приложения
        await user_service.create_user_table()

        # Инициализация базы данных пользовательских данных
        logger.info("Initializing data database...")
        await data_database_service.initialize()

        logger.info("Application startup completed successfully")

        yield

    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    finally:
        # Закрытие подключений при завершении работы
        logger.info("Shutting down application...")

        try:
            await app_database_service.close()
        except Exception as e:
            logger.error(f"Error closing application database: {e}")

        try:
            await data_database_service.close()
        except Exception as e:
            logger.error(f"Error closing data database: {e}")

        logger.info("Application shutdown completed")


# Создаем приложение FastAPI
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Backend API для CloverdashBot с разделенными базами данных",
    lifespan=lifespan,
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роуты
app.include_router(router)


# Корневой endpoint
@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "CloverdashBot Backend API",
        "version": settings.api_version,
        "databases": {
            "application_db": app_database_service.is_connected,
            "data_db": data_database_service.is_connected,
        },
    }


if __name__ == "__main__":
    # Запуск сервера
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,  # Для разработки
        log_level=settings.log_level.lower(),
    )
