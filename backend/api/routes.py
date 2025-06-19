from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging

from services.database import database_service
from services.llm_service import llm_service
from models.schemas import (
    QueryRequest,
    QueryResponse,
    DatabaseQueryResult,
    LLMQueryResponse,
    HealthResponse,
    SchemaResponse,
)

logger = logging.getLogger(__name__)

# Создаем роутер
router = APIRouter()


@router.get("/", response_model=Dict[str, str])
async def root():
    """Корневой endpoint"""
    return {"message": "CloverdashBot Backend API", "version": "1.0.0", "status": "running"}


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Проверка состояния сервисов"""
    try:
        # Проверяем состояние базы данных
        db_status = await database_service.test_connection() if database_service.is_connected else False

        # Проверяем состояние LLM сервиса
        llm_status = await llm_service.test_connection()

        overall_status = "healthy" if db_status and llm_status else "unhealthy"

        return HealthResponse(
            status=overall_status,
            database_connected=db_status,
            llm_service_available=llm_status,
            timestamp=None,  # Pydantic автоматически установит текущее время
        )

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(status="unhealthy", database_connected=False, llm_service_available=False, timestamp=None)


@router.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """
    Выполняет запрос к базе данных через LLM

    Args:
        request: Запрос пользователя

    Returns:
        QueryResponse: Результат выполнения запроса
    """
    try:
        # Генерируем SQL запрос с помощью LLM
        llm_response = await llm_service.generate_sql_query(request.query)

        # Выполняем SQL запрос в базе данных
        db_result = await database_service.execute_query(llm_response.sql_query)

        # Формируем ответ
        response = QueryResponse(
            success=True,
            message="Запрос выполнен успешно",
            sql_query=llm_response.sql_query,
            explanation=llm_response.explanation,
            data=db_result.data,
            columns=db_result.columns,
            row_count=db_result.row_count,
            execution_time=db_result.execution_time + llm_response.execution_time,
            llm_time=llm_response.execution_time,
            db_time=db_result.execution_time,
        )

        logger.info(f"Query executed successfully: {request.query[:100]}...")
        return response

    except Exception as e:
        error_message = str(e)
        logger.error(f"Query execution failed: {error_message}")

        # Возвращаем ошибку
        return QueryResponse(
            success=False,
            message=f"Ошибка выполнения запроса: {error_message}",
            sql_query=None,
            explanation=None,
            data=[],
            columns=[],
            row_count=0,
            execution_time=0,
            llm_time=0,
            db_time=0,
        )


@router.get("/schema", response_model=SchemaResponse)
async def get_database_schema():
    """
    Возвращает схему базы данных

    Returns:
        SchemaResponse: Схема базы данных
    """
    try:
        if not database_service.is_connected:
            raise HTTPException(status_code=503, detail="База данных недоступна")

        schema = await database_service.get_database_schema()

        return SchemaResponse(
            success=True, message="Схема базы данных получена успешно", schema=schema, table_count=len(schema)
        )

    except Exception as e:
        logger.error(f"Failed to get database schema: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения схемы: {str(e)}")


@router.post("/sql", response_model=DatabaseQueryResult)
async def execute_raw_sql(sql_query: str):
    """
    Выполняет прямой SQL запрос (только для отладки)

    Args:
        sql_query: SQL запрос для выполнения

    Returns:
        DatabaseQueryResult: Результат выполнения запроса
    """
    try:
        if not database_service.is_connected:
            raise HTTPException(status_code=503, detail="База данных недоступна")

        # Простая валидация безопасности
        sql_upper = sql_query.upper().strip()
        if not sql_upper.startswith("SELECT"):
            raise HTTPException(status_code=400, detail="Разрешены только SELECT запросы")

        result = await database_service.execute_query(sql_query)
        return result

    except Exception as e:
        logger.error(f"Raw SQL execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка выполнения SQL: {str(e)}")


@router.get("/info", response_model=Dict[str, Any])
async def get_service_info():
    """
    Возвращает информацию о сервисах

    Returns:
        Dict: Информация о сервисах
    """
    return {
        "database": {"connected": database_service.is_connected, "service": "Database Service"},
        "llm": llm_service.get_service_info(),
    }
