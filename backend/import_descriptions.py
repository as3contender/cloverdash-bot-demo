#!/usr/bin/env python3
"""
Скрипт для импорта описаний таблиц из column_descriptions.json в базу данных приложения
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Добавляем путь к backend для импорта модулей
sys.path.append(str(Path(__file__).parent))

from services.app_database import app_database_service
from services.data_database import data_database_service
from config.settings import DB_SCHEMA_CONTEXT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def import_column_descriptions():
    """Импорт описаний колонок из column_descriptions.json"""

    try:
        # Инициализируем подключения к базам данных
        logger.info("Initializing database connections...")
        await app_database_service.initialize()
        await data_database_service.initialize()

        # Создаем таблицы приложения, если их нет
        await app_database_service.create_app_tables()

        # Получаем данные из column_descriptions.json
        if not DB_SCHEMA_CONTEXT:
            logger.error("column_descriptions.json not found or empty")
            return False

        logger.info(f"Found {len(DB_SCHEMA_CONTEXT)} column descriptions")

        # Получаем имя текущей базы данных пользовательских данных
        database_name = data_database_service.get_database_name()
        logger.info(f"Target database: {database_name}")

        # Получаем схему базы данных для получения реальных таблиц и представлений
        try:
            schema = await data_database_service.get_database_schema(include_views=True)
            real_objects = list(schema.keys())
            tables_count = sum(1 for name in real_objects if schema[name].get("object_type") == "table")
            views_count = sum(1 for name in real_objects if schema[name].get("object_type") == "view")
            logger.info(
                f"Found {len(real_objects)} objects in data database: {tables_count} tables, {views_count} views"
            )
        except Exception as e:
            logger.warning(f"Could not get database schema: {str(e)}")
            real_objects = []
            schema = {}

        # Создаем описания для каждого реального объекта (таблицы и представления)
        success_count = 0
        for object_name in real_objects:
            try:
                object_info = schema.get(object_name, {})
                object_type = object_info.get("object_type", "table")
                schema_name = object_info.get("schema_name", "public")

                # Создаем описание объекта на основе column_descriptions.json
                object_description = {
                    "description": f"{object_type.capitalize()} данных {object_name}",
                    "columns": DB_SCHEMA_CONTEXT,
                    "imported_from": "column_descriptions.json",
                    "import_date": str(asyncio.get_event_loop().time()),
                    "object_type": object_type,
                    "schema_name": schema_name,
                }

                # Сохраняем описание
                success = await app_database_service.save_table_description(
                    database_name, object_name, object_description, schema_name, object_type
                )

                if success:
                    logger.info(f"✓ Imported description for {object_type}: {schema_name}.{object_name}")
                    success_count += 1
                else:
                    logger.error(f"✗ Failed to import description for {object_type}: {object_name}")

            except Exception as e:
                logger.error(f"Error importing description for {object_type} {object_name}: {str(e)}")

        # Также создаем общее описание для случаев, когда нет подключения к data_database
        try:
            generic_description = {
                "description": "Общие описания колонок из column_descriptions.json",
                "columns": DB_SCHEMA_CONTEXT,
                "imported_from": "column_descriptions.json",
                "import_date": str(asyncio.get_event_loop().time()),
                "note": "Это общее описание, используемое как fallback",
                "object_type": "generic",
                "schema_name": "public",
            }

            success = await app_database_service.save_table_description(
                database_name, "generic_columns", generic_description, "public", "generic"
            )

            if success:
                logger.info("✓ Imported generic column descriptions")
                success_count += 1

        except Exception as e:
            logger.error(f"Error importing generic description: {str(e)}")

        logger.info(f"Import completed: {success_count} descriptions imported")
        return success_count > 0

    except Exception as e:
        logger.error(f"Import failed: {str(e)}")
        return False

    finally:
        # Закрываем подключения
        await app_database_service.close()
        await data_database_service.close()


async def list_current_descriptions():
    """Вывод текущих описаний таблиц"""

    try:
        # Инициализируем подключение к базе приложения
        await app_database_service.initialize()

        # Получаем все описания
        descriptions = await app_database_service.get_all_table_descriptions()

        if not descriptions:
            logger.info("No table descriptions found")
            return

        logger.info(f"Found {len(descriptions)} table descriptions:")
        for key, desc in descriptions.items():
            if isinstance(desc, dict):
                description_text = desc.get("description", "No description")
                object_type = desc.get("object_type", "unknown")
                schema_name = desc.get("schema_name", "unknown")
                logger.info(f"  {key} ({object_type}): {description_text[:100]}...")
                if "columns" in desc:
                    logger.info(f"    Schema: {schema_name}, Columns: {len(desc['columns'])}")
            else:
                logger.info(f"  {key}: {str(desc)[:100]}...")

    except Exception as e:
        logger.error(f"Failed to list descriptions: {str(e)}")

    finally:
        await app_database_service.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Import table descriptions")
    parser.add_argument(
        "action", choices=["import", "list"], help="Action to perform: import descriptions or list current descriptions"
    )

    args = parser.parse_args()

    if args.action == "import":
        success = asyncio.run(import_column_descriptions())
        if success:
            logger.info("Import completed successfully!")
            sys.exit(0)
        else:
            logger.error("Import failed!")
            sys.exit(1)
    elif args.action == "list":
        asyncio.run(list_current_descriptions())
