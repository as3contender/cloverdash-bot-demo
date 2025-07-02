from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import logging

from services.data_database import data_database_service
from services.app_database import app_database_service
from services.llm_service import llm_service
from services.security import security_service
from services.user_service import user_service
from models.base import QueryRequest, QueryResponse
from models.database import SchemaResponse, DatabaseQueryResult

logger = logging.getLogger(__name__)

# Создаем роутер для database endpoints
database_router = APIRouter(prefix="/database", tags=["Database"])


@database_router.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest, user_id: str = Depends(security_service.get_current_user_id)):
    """
    Выполняет запрос к базе данных через LLM

    Требует аутентификации для доступа к базе данных.

    Args:
        request: Запрос пользователя
        user_id: ID аутентифицированного пользователя

    Returns:
        QueryResponse: Результат выполнения запроса
    """
    try:
        # Устанавливаем user_id из токена аутентификации
        request.user_id = user_id

        # Генерируем SQL запрос с помощью LLM
        llm_response = await llm_service.generate_sql_query(request.query)

        # Выполняем SQL запрос в базе данных пользовательских данных
        db_result = await data_database_service.execute_query(llm_response.sql_query)

        # Сохраняем историю запроса
        await user_service.save_user_query_history(
            user_id=user_id,
            query=request.query,
            sql_query=llm_response.sql_query,
            result_count=db_result.row_count,
            execution_time=db_result.execution_time + llm_response.execution_time,
            success=True,
        )

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

        logger.info(f"Query executed successfully by user {user_id}: {request.query[:100]}...")
        return response

    except Exception as e:
        error_message = str(e)
        logger.error(f"Query execution failed for user {user_id}: {error_message}")

        # Сохраняем историю неудачного запроса
        try:
            await user_service.save_user_query_history(
                user_id=user_id,
                query=request.query,
                sql_query=getattr(llm_response, "sql_query", None) if "llm_response" in locals() else None,
                result_count=0,
                execution_time=0,
                success=False,
                error_message=error_message,
            )
        except Exception as save_error:
            logger.error(f"Failed to save error query history: {save_error}")

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


@database_router.get("/schema", response_model=SchemaResponse)
async def get_database_schema(user_id: str = Depends(security_service.get_current_user_id)):
    """
    Возвращает схему базы данных пользовательских данных

    Требует аутентификации.

    Args:
        user_id: ID аутентифицированного пользователя

    Returns:
        SchemaResponse: Схема базы данных
    """
    try:
        if not data_database_service.is_connected:
            raise HTTPException(status_code=503, detail="База данных недоступна")

        schema = await data_database_service.get_database_schema()

        logger.info(f"Database schema requested by user: {user_id}")
        return SchemaResponse(
            success=True, message="Схема базы данных получена успешно", database_schema=schema, table_count=len(schema)
        )

    except Exception as e:
        logger.error(f"Failed to get database schema for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения схемы: {str(e)}")


@database_router.post("/sql", response_model=DatabaseQueryResult)
async def execute_raw_sql(sql_query: str, user_id: str = Depends(security_service.get_current_user_id)):
    """
    Выполняет прямой SQL запрос (только для отладки)

    Требует аутентификации.

    Args:
        sql_query: SQL запрос для выполнения
        user_id: ID аутентифицированного пользователя

    Returns:
        DatabaseQueryResult: Результат выполнения запроса
    """
    try:
        if not data_database_service.is_connected:
            raise HTTPException(status_code=503, detail="База данных недоступна")

        # Простая валидация безопасности
        sql_upper = sql_query.upper().strip()
        if not sql_upper.startswith("SELECT"):
            raise HTTPException(status_code=400, detail="Разрешены только SELECT запросы")

        result = await data_database_service.execute_query(sql_query)

        # Сохраняем историю прямого SQL запроса
        await user_service.save_user_query_history(
            user_id=user_id,
            query=f"[DIRECT SQL] {sql_query}",
            sql_query=sql_query,
            result_count=result.row_count,
            execution_time=result.execution_time,
            success=True,
        )

        logger.info(f"Raw SQL executed by user {user_id}: {sql_query[:100]}...")
        return result

    except Exception as e:
        error_message = str(e)
        logger.error(f"Raw SQL execution failed for user {user_id}: {error_message}")

        # Сохраняем историю неудачного SQL запроса
        try:
            await user_service.save_user_query_history(
                user_id=user_id,
                query=f"[DIRECT SQL] {sql_query}",
                sql_query=sql_query,
                result_count=0,
                execution_time=0,
                success=False,
                error_message=error_message,
            )
        except Exception as save_error:
            logger.error(f"Failed to save error SQL history: {save_error}")

        raise HTTPException(status_code=500, detail=f"Ошибка выполнения SQL: {error_message}")


@database_router.get("/history", response_model=list)
async def get_query_history(user_id: str = Depends(security_service.get_current_user_id), limit: int = 50):
    """
    Получение истории запросов пользователя

    Args:
        user_id: ID аутентифицированного пользователя
        limit: Максимальное количество записей

    Returns:
        list: История запросов пользователя
    """
    try:
        history = await user_service.get_user_query_history(user_id, limit)
        logger.info(f"Query history requested by user {user_id}: {len(history)} records")
        return history

    except Exception as e:
        logger.error(f"Failed to get query history for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения истории: {str(e)}")


@database_router.get("/table/{table_name}/sample", response_model=DatabaseQueryResult)
async def get_table_sample(
    table_name: str, user_id: str = Depends(security_service.get_current_user_id), limit: int = 5
):
    """
    Получение примера данных из таблицы

    Args:
        table_name: Имя таблицы
        user_id: ID аутентифицированного пользователя
        limit: Количество строк для примера

    Returns:
        DatabaseQueryResult: Пример данных из таблицы
    """
    try:
        if not data_database_service.is_connected:
            raise HTTPException(status_code=503, detail="База данных недоступна")

        result = await data_database_service.get_table_sample(table_name, limit)
        logger.info(f"Table sample requested by user {user_id}: {table_name}")
        return result

    except Exception as e:
        logger.error(f"Failed to get table sample for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения примера данных: {str(e)}")
