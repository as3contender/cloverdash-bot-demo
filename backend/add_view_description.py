#!/usr/bin/env python3
"""
Скрипт для добавления описания представления bills_view
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Добавляем путь к backend для импорта модулей
sys.path.append(str(Path(__file__).parent))

from services.app_database import app_database_service
from config.settings import DB_SCHEMA_CONTEXT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def add_view_description():
    """Добавление описания для представления bills_view"""

    try:
        # Инициализируем подключение к базе приложения
        logger.info("Initializing app database connection...")
        await app_database_service.initialize()

        # Получаем данные из column_descriptions.json
        if not DB_SCHEMA_CONTEXT:
            logger.error("column_descriptions.json not found or empty")
            return False

        logger.info(f"Found {len(DB_SCHEMA_CONTEXT)} column descriptions")

        # Параметры представления
        database_name = "test1"
        schema_name = "demo1"
        view_name = "bills_view"
        object_type = "view"

        # Создаем описание представления
        view_description = {
            "description": "Представление bills_view для анализа данных о счетах и продажах",
            "columns": DB_SCHEMA_CONTEXT,
            "object_type": object_type,
            "schema_name": schema_name,
            "imported_from": "column_descriptions.json",
            "created_manually": True,
            "notes": "Представление для консолидированного анализа данных о продажах, товарах и платежах",
        }

        # Сохраняем описание
        logger.info(f"Saving description for {object_type}: {database_name}.{schema_name}.{view_name}")

        success = await app_database_service.save_table_description(
            database_name, view_name, view_description, schema_name, object_type
        )

        if success:
            logger.info(f"✓ View description saved successfully: {database_name}.{schema_name}.{view_name}")

            # Проверяем что описание сохранилось
            saved_desc = await app_database_service.get_table_description(database_name, view_name, schema_name)

            if saved_desc:
                logger.info("✓ Description verification successful")
                logger.info(f"  Description: {saved_desc.get('description', 'N/A')}")
                logger.info(f"  Object type: {saved_desc.get('object_type', 'N/A')}")
                logger.info(f"  Schema: {saved_desc.get('schema_name', 'N/A')}")
                logger.info(f"  Columns count: {len(saved_desc.get('columns', {}))}")
            else:
                logger.warning("⚠ Could not verify saved description")

            return True
        else:
            logger.error(f"✗ Failed to save view description")
            return False

    except Exception as e:
        logger.error(f"Failed to add view description: {str(e)}")
        return False

    finally:
        await app_database_service.close()


async def list_view_descriptions():
    """Список всех описаний представлений"""

    try:
        await app_database_service.initialize()

        # Получаем только описания представлений
        descriptions = await app_database_service.get_all_table_descriptions(object_type="view")

        if not descriptions:
            logger.info("No view descriptions found")
            return

        logger.info(f"Found {len(descriptions)} view descriptions:")
        for key, desc in descriptions.items():
            if isinstance(desc, dict):
                description_text = desc.get("description", "No description")
                object_type = desc.get("object_type", "unknown")
                schema_name = desc.get("schema_name", "unknown")
                logger.info(f"  {key} ({object_type}): {description_text}")
                if "columns" in desc:
                    logger.info(f"    Schema: {schema_name}, Columns: {len(desc['columns'])}")

    except Exception as e:
        logger.error(f"Failed to list view descriptions: {str(e)}")

    finally:
        await app_database_service.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Add or list view descriptions")
    parser.add_argument(
        "action",
        choices=["add", "list"],
        help="Action to perform: add view description or list current view descriptions",
    )

    args = parser.parse_args()

    if args.action == "add":
        success = asyncio.run(add_view_description())
        if success:
            logger.info("View description added successfully!")
            sys.exit(0)
        else:
            logger.error("Failed to add view description!")
            sys.exit(1)
    elif args.action == "list":
        asyncio.run(list_view_descriptions())
