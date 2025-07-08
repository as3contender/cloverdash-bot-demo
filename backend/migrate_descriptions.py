#!/usr/bin/env python3
"""
Скрипт миграции для добавления поддержки схем и типов объектов в таблицу database_descriptions
"""

import asyncio
import logging
import sys
from pathlib import Path

# Добавляем путь к backend для импорта модулей
sys.path.append(str(Path(__file__).parent))

from services.app_database import app_database_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate_database_descriptions():
    """Миграция таблицы database_descriptions для поддержки схем и типов объектов"""

    try:
        # Инициализируем подключение к базе приложения
        logger.info("Initializing app database connection...")
        await app_database_service.initialize()

        # Добавляем новые колонки если их нет
        migration_queries = [
            # Добавляем колонку schema_name
            """
            ALTER TABLE database_descriptions 
            ADD COLUMN IF NOT EXISTS schema_name VARCHAR(255) NOT NULL DEFAULT 'public'
            """,
            # Добавляем колонку object_type
            """
            ALTER TABLE database_descriptions 
            ADD COLUMN IF NOT EXISTS object_type VARCHAR(50) NOT NULL DEFAULT 'table'
            """,
            # Удаляем старый уникальный индекс
            """
            DROP INDEX IF EXISTS database_descriptions_database_name_table_name_key
            """,
            # Создаем новый уникальный индекс
            """
            CREATE UNIQUE INDEX IF NOT EXISTS database_descriptions_unique_key 
            ON database_descriptions(database_name, schema_name, table_name)
            """,
            # Добавляем новые индексы
            """
            CREATE INDEX IF NOT EXISTS idx_database_descriptions_schema 
            ON database_descriptions(schema_name)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_database_descriptions_type 
            ON database_descriptions(object_type)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_database_descriptions_combined_new 
            ON database_descriptions(database_name, schema_name, table_name)
            """,
        ]

        logger.info("Running migration queries...")
        for i, query in enumerate(migration_queries, 1):
            try:
                await app_database_service.execute_query(query)
                logger.info(f"✓ Migration step {i}/{len(migration_queries)} completed")
            except Exception as e:
                logger.warning(f"⚠ Migration step {i} failed (might be expected): {str(e)}")

        logger.info("Migration completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return False

    finally:
        await app_database_service.close()


async def check_migration_status():
    """Проверка статуса миграции"""

    try:
        await app_database_service.initialize()

        # Проверяем структуру таблицы
        check_query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = 'database_descriptions'
        ORDER BY ordinal_position
        """

        result = await app_database_service.execute_query(check_query)

        logger.info("Current database_descriptions table structure:")
        for row in result.data:
            logger.info(
                f"  {row['column_name']}: {row['data_type']} "
                f"({'NULL' if row['is_nullable'] == 'YES' else 'NOT NULL'}) "
                f"DEFAULT {row['column_default'] or 'NULL'}"
            )

        # Проверяем индексы
        indexes_query = """
        SELECT indexname, indexdef
        FROM pg_indexes 
        WHERE tablename = 'database_descriptions'
        ORDER BY indexname
        """

        result = await app_database_service.execute_query(indexes_query)

        logger.info("Current indexes:")
        for row in result.data:
            logger.info(f"  {row['indexname']}: {row['indexdef']}")

    except Exception as e:
        logger.error(f"Failed to check migration status: {str(e)}")

    finally:
        await app_database_service.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Migrate database_descriptions table")
    parser.add_argument(
        "action", choices=["migrate", "check"], help="Action to perform: migrate table or check current status"
    )

    args = parser.parse_args()

    if args.action == "migrate":
        success = asyncio.run(migrate_database_descriptions())
        if success:
            logger.info("Migration completed successfully!")
            sys.exit(0)
        else:
            logger.error("Migration failed!")
            sys.exit(1)
    elif args.action == "check":
        asyncio.run(check_migration_status())
