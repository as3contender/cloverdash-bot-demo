from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn
from contextlib import asynccontextmanager

from config.settings import settings
from api.routes import router
from services.database import database_service
from services.llm_service import llm_service


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
    # Startup
    logger.info("Starting CloverdashBot Backend...")

    try:
        # Инициализируем подключение к базе данных
        await database_service.initialize()
        logger.info("Database service initialized")
    except Exception as e:
        logger.warning(f"Database initialization failed: {str(e)}")
        logger.warning("Application will continue without database connection")

    # Инициализируем LLM сервис (уже инициализирован при импорте)
    logger.info("LLM service ready")

    logger.info("Backend startup completed")

    yield

    # Shutdown
    logger.info("Shutting down CloverdashBot Backend...")

    # Закрываем подключение к базе данных
    try:
        await database_service.close()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {str(e)}")

    logger.info("Backend shutdown completed")


# Создаем приложение FastAPI
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Backend API для CloverdashBot - телеграм-бот для работы с базой данных через естественный язык",
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


if __name__ == "__main__":
    # Запуск сервера
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,  # Для разработки
        log_level=settings.log_level.lower(),
    )
