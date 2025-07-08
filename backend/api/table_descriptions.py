from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
import logging

from services.app_database import app_database_service
from services.data_database import data_database_service
from services.security import security_service
from models.database import TableDescriptionRequest, TableDescriptionResponse, DatabaseInfoResponse

logger = logging.getLogger(__name__)

# Создаем роутер для управления описаниями таблиц
descriptions_router = APIRouter(prefix="/descriptions", tags=["Table Descriptions"])


@descriptions_router.post("/table/{database_name}/{schema_name}/{table_name}")
async def save_table_description(
    database_name: str,
    schema_name: str,
    table_name: str,
    description: TableDescriptionRequest,
    user_id: str = Depends(security_service.get_current_user_id),
):
    """
    Сохранение описания таблицы или представления

    Args:
        database_name: Имя базы данных
        schema_name: Имя схемы
        table_name: Имя таблицы или представления
        description: Описание объекта в формате column_descriptions.json
        user_id: ID аутентифицированного пользователя

    Returns:
        Dict: Результат сохранения
    """
    try:
        # Используем схему и тип из URL параметров, но позволяем переопределить их в теле запроса
        actual_schema = description.schema_name if description.schema_name != "public" else schema_name
        actual_object_type = description.object_type

        success = await app_database_service.save_table_description(
            database_name, table_name, description.model_dump(), actual_schema, actual_object_type
        )

        if success:
            logger.info(
                f"{actual_object_type.capitalize()} description saved by user {user_id}: {database_name}.{actual_schema}.{table_name}"
            )
            return {
                "success": True,
                "message": f"Описание {actual_object_type} {database_name}.{actual_schema}.{table_name} сохранено успешно",
            }
        else:
            raise HTTPException(status_code=500, detail=f"Не удалось сохранить описание {actual_object_type}")

    except Exception as e:
        logger.error(f"Failed to save table description: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения описания: {str(e)}")


@descriptions_router.get("/table/{database_name}/{schema_name}/{table_name}", response_model=TableDescriptionResponse)
async def get_table_description(
    database_name: str, schema_name: str, table_name: str, user_id: str = Depends(security_service.get_current_user_id)
):
    """
    Получение описания таблицы или представления

    Args:
        database_name: Имя базы данных
        schema_name: Имя схемы
        table_name: Имя таблицы или представления
        user_id: ID аутентифицированного пользователя

    Returns:
        TableDescriptionResponse: Описание объекта
    """
    try:
        description = await app_database_service.get_table_description(database_name, table_name, schema_name)

        if description:
            object_type = description.get("object_type", "table") if isinstance(description, dict) else "table"

            return {
                "success": True,
                "database_name": database_name,
                "schema_name": schema_name,
                "table_name": table_name,
                "object_type": object_type,
                "description": description,
            }
        else:
            raise HTTPException(
                status_code=404, detail=f"Описание объекта {database_name}.{schema_name}.{table_name} не найдено"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get table description: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения описания: {str(e)}")


@descriptions_router.get("/database/{database_name}")
async def get_database_descriptions(
    database_name: str,
    schema_name: str = "public",
    object_type: str = None,
    user_id: str = Depends(security_service.get_current_user_id),
):
    """
    Получение всех описаний таблиц и представлений базы данных

    Args:
        database_name: Имя базы данных
        schema_name: Имя схемы (по умолчанию 'public')
        object_type: Тип объекта для фильтрации (table, view, generic)
        user_id: ID аутентифицированного пользователя

    Returns:
        Dict: Все описания объектов базы данных
    """
    try:
        descriptions = await app_database_service.get_all_table_descriptions(
            database_name=database_name, schema_name=schema_name, object_type=object_type
        )

        # Подсчитываем объекты по типам
        type_counts = {}
        for desc in descriptions.values():
            if isinstance(desc, dict) and "object_type" in desc:
                obj_type = desc["object_type"]
                type_counts[obj_type] = type_counts.get(obj_type, 0) + 1

        return {
            "success": True,
            "database_name": database_name,
            "schema_name": schema_name,
            "object_type_filter": object_type,
            "total_count": len(descriptions),
            "type_counts": type_counts,
            "descriptions": descriptions,
        }

    except Exception as e:
        logger.error(f"Failed to get database descriptions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения описаний: {str(e)}")


@descriptions_router.get("/all")
async def get_all_descriptions(user_id: str = Depends(security_service.get_current_user_id)):
    """
    Получение всех описаний таблиц всех баз данных

    Args:
        user_id: ID аутентифицированного пользователя

    Returns:
        Dict: Все описания таблиц
    """
    try:
        descriptions = await app_database_service.get_all_table_descriptions()

        return {"success": True, "total_count": len(descriptions), "descriptions": descriptions}

    except Exception as e:
        logger.error(f"Failed to get all descriptions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения описаний: {str(e)}")


@descriptions_router.delete("/table/{database_name}/{schema_name}/{table_name}")
async def delete_table_description(
    database_name: str, schema_name: str, table_name: str, user_id: str = Depends(security_service.get_current_user_id)
):
    """
    Удаление описания таблицы или представления

    Args:
        database_name: Имя базы данных
        schema_name: Имя схемы
        table_name: Имя таблицы или представления
        user_id: ID аутентифицированного пользователя

    Returns:
        Dict: Результат удаления
    """
    try:
        success = await app_database_service.delete_table_description(database_name, table_name, schema_name)

        if success:
            logger.info(f"Object description deleted by user {user_id}: {database_name}.{schema_name}.{table_name}")
            return {
                "success": True,
                "message": f"Описание объекта {database_name}.{schema_name}.{table_name} удалено успешно",
            }
        else:
            raise HTTPException(status_code=500, detail="Не удалось удалить описание объекта")

    except Exception as e:
        logger.error(f"Failed to delete table description: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка удаления описания: {str(e)}")


@descriptions_router.post("/import/column-descriptions")
async def import_column_descriptions(
    database_name: str, table_name: str, user_id: str = Depends(security_service.get_current_user_id)
):
    """
    Импорт описаний из column_descriptions.json в таблицу описаний

    Args:
        database_name: Имя базы данных
        table_name: Имя таблицы (будет создано виртуальное описание)
        user_id: ID аутентифицированного пользователя

    Returns:
        Dict: Результат импорта
    """
    try:
        from config.settings import DB_SCHEMA_CONTEXT

        if not DB_SCHEMA_CONTEXT:
            raise HTTPException(status_code=404, detail="column_descriptions.json не найден или пуст")

        # Создаем описание таблицы из column_descriptions.json
        table_description = {
            "description": f"Таблица {table_name} (импортировано из column_descriptions.json)",
            "columns": DB_SCHEMA_CONTEXT,
        }

        success = await app_database_service.save_table_description(database_name, table_name, table_description)

        if success:
            logger.info(f"Column descriptions imported by user {user_id}: {database_name}.{table_name}")
            return {
                "success": True,
                "message": f"Описания колонок импортированы для таблицы {database_name}.{table_name}",
                "imported_columns": len(DB_SCHEMA_CONTEXT),
            }
        else:
            raise HTTPException(status_code=500, detail="Не удалось сохранить импортированные описания")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to import column descriptions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка импорта описаний: {str(e)}")


@descriptions_router.get("/current-data-database", response_model=DatabaseInfoResponse)
async def get_current_data_database_info(user_id: str = Depends(security_service.get_current_user_id)):
    """
    Получение информации о текущей базе данных пользовательских данных

    Args:
        user_id: ID аутентифицированного пользователя

    Returns:
        Dict: Информация о текущей базе данных
    """
    try:
        database_name = data_database_service.get_database_name()
        is_connected = data_database_service.is_connected

        # Получаем количество сохраненных описаний для этой базы
        descriptions = await app_database_service.get_all_table_descriptions(database_name)

        return {
            "success": True,
            "database_name": database_name,
            "is_connected": is_connected,
            "saved_descriptions_count": len(descriptions),
        }

    except Exception as e:
        logger.error(f"Failed to get current data database info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения информации о базе данных: {str(e)}")
