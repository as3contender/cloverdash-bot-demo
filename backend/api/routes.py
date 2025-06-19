from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import logging
import time

from models.schemas import QueryRequest, QueryResponse, HealthResponse, ErrorResponse
from services.llm_service import llm_service
from services.database import database_service
from config.settings import settings

logger = logging.getLogger(__name__)

# Создаем роутер для API
router = APIRouter()


@router.get("/", summary="Информация о API")
async def root():
    """Базовая информация о API"""
    return {"message": "CloverdashBot Backend API", "version": settings.api_version, "status": "running"}


@router.get("/health", response_model=HealthResponse, summary="Проверка состояния сервиса")
async def health_check():
    """
    Проверка состояния сервиса и его компонентов
    """
    try:
        # Проверяем подключение к базе данных
        db_connected = await database_service.test_connection()

        return HealthResponse(
            status="healthy" if db_connected else "degraded",
            timestamp=datetime.now(),
            version=settings.api_version,
            database_connected=db_connected,
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(
            status="unhealthy", timestamp=datetime.now(), version=settings.api_version, database_connected=False
        )


@router.post("/query", response_model=QueryResponse, summary="Обработка запроса пользователя")
async def process_query(request: QueryRequest):
    """
    Обрабатывает вопрос пользователя, создает SQL запрос с помощью LLM
    и возвращает результат из базы данных
    """
    start_time = time.time()

    try:
        logger.info(f"Processing query from user {request.user_id}: {request.question}")

        # Генерируем SQL запрос с помощью LLM
        sql_query, llm_time = llm_service.generate_sql_query(question=request.question, user_id=request.user_id)

        # Валидируем SQL запрос
        if not llm_service.validate_sql_query(sql_query):
            raise HTTPException(status_code=400, detail="Сгенерированный SQL запрос не прошел валидацию безопасности")

        # Выполняем запрос к базе данных
        if database_service.is_connected:
            try:
                db_result = await database_service.execute_query(sql_query)

                # Формируем читаемый ответ
                if db_result.row_count == 0:
                    answer = "По вашему запросу не найдено результатов."
                elif db_result.row_count == 1 and len(db_result.columns) == 1:
                    # Простой ответ для одиночного значения
                    value = db_result.data[0][db_result.columns[0]]
                    answer = f"Результат: {value}"
                else:
                    # Сложный ответ с таблицей данных
                    answer = f"Найдено {db_result.row_count} записей:\n\n"

                    # Добавляем первые несколько строк для предварительного просмотра
                    preview_rows = min(5, db_result.row_count)
                    for i in range(preview_rows):
                        row_data = db_result.data[i]
                        row_text = ", ".join([f"{col}: {row_data[col]}" for col in db_result.columns])
                        answer += f"• {row_text}\n"

                    if db_result.row_count > preview_rows:
                        answer += f"\n... и еще {db_result.row_count - preview_rows} записей"

                total_time = time.time() - start_time

                return QueryResponse(answer=answer, sql_query=sql_query, success=True, execution_time=total_time)

            except Exception as db_error:
                logger.error(f"Database error: {str(db_error)}")
                raise HTTPException(status_code=500, detail=f"Ошибка выполнения запроса к базе данных: {str(db_error)}")
        else:
            # База данных недоступна - возвращаем только SQL запрос
            logger.warning("Database not connected, returning SQL query only")
            total_time = time.time() - start_time

            return QueryResponse(
                answer=f"База данных временно недоступна. Сгенерированный SQL запрос: {sql_query}",
                sql_query=sql_query,
                success=True,
                execution_time=total_time,
            )

    except HTTPException:
        # Повторно выбрасываем HTTP исключения
        raise
    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"Query processing failed after {total_time:.2f}s: {str(e)}")

        return QueryResponse(
            answer="Произошла ошибка при обработке запроса.",
            sql_query=None,
            success=False,
            execution_time=total_time,
            error_message=str(e),
        )


@router.get("/schema", summary="Получение схемы базы данных")
async def get_database_schema():
    """
    Возвращает схему базы данных (список таблиц и колонок)
    """
    try:
        if not database_service.is_connected:
            raise HTTPException(status_code=503, detail="База данных недоступна")

        schema = await database_service.get_database_schema()
        return {"schema": schema, "table_count": len(schema)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get database schema: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения схемы базы данных: {str(e)}")
