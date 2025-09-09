#!/usr/bin/env python3
"""
Скрипт для добавления описания таблицы users в database_descriptions.
"""

import asyncio
import logging
import sys
import os
import json

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.app_database import app_database_service

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def add_users_table_description(database_name: str, schema_name: str = "demo1"):
    """Добавляет описание таблицы users в database_descriptions"""
    logger.info(f"📝 Добавление описания таблицы users в database_descriptions")
    
    try:
        # 1. Проверяем, существует ли уже описание
        check_query = """
        SELECT id, table_description, created_at
        FROM database_descriptions 
        WHERE database_name = $1 
        AND schema_name = $2 
        AND table_name = 'users'
        """
        
        check_result = await app_database_service.execute_query(check_query, [database_name, schema_name])
        
        if check_result.data:
            logger.info(f"✅ Описание таблицы users уже существует:")
            for desc in check_result.data:
                logger.info(f"   Description: {desc['table_description']}")
                logger.info(f"   Created: {desc['created_at']}")
            return True
        
        # 2. Создаем описание таблицы users
        users_description = {
            "description": "Таблица пользователей системы",
            "object_type": "table",
            "columns": {
                "id": {
                    "description": "Уникальный идентификатор пользователя",
                    "datatype": "uuid",
                    "type": "uuid",
                    "nullable": False,
                    "default": "gen_random_uuid()"
                },
                "username": {
                    "description": "Имя пользователя",
                    "datatype": "character varying",
                    "type": "character varying",
                    "nullable": True,
                    "default": None
                },
                "email": {
                    "description": "Email адрес пользователя",
                    "datatype": "character varying",
                    "type": "character varying",
                    "nullable": True,
                    "default": None
                },
                "full_name": {
                    "description": "Полное имя пользователя",
                    "datatype": "character varying",
                    "type": "character varying",
                    "nullable": True,
                    "default": None
                },
                "hashed_password": {
                    "description": "Хэшированный пароль пользователя",
                    "datatype": "character varying",
                    "type": "character varying",
                    "nullable": True,
                    "default": None
                },
                "telegram_id": {
                    "description": "Telegram ID пользователя",
                    "datatype": "character varying",
                    "type": "character varying",
                    "nullable": True,
                    "default": None
                },
                "telegram_username": {
                    "description": "Telegram username пользователя",
                    "datatype": "character varying",
                    "type": "character varying",
                    "nullable": True,
                    "default": None
                },
                "is_active": {
                    "description": "Статус активности пользователя",
                    "datatype": "boolean",
                    "type": "boolean",
                    "nullable": False,
                    "default": "true"
                },
                "created_at": {
                    "description": "Дата создания записи",
                    "datatype": "timestamp without time zone",
                    "type": "timestamp without time zone",
                    "nullable": False,
                    "default": "CURRENT_TIMESTAMP"
                },
                "updated_at": {
                    "description": "Дата последнего обновления записи",
                    "datatype": "timestamp without time zone",
                    "type": "timestamp without time zone",
                    "nullable": False,
                    "default": "CURRENT_TIMESTAMP"
                }
            }
        }
        
        # 3. Добавляем описание в database_descriptions
        insert_query = """
        INSERT INTO database_descriptions (database_name, schema_name, table_name, object_type, table_description, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """
        
        await app_database_service.execute_query(insert_query, [
            database_name, 
            schema_name, 
            'users', 
            'table', 
            json.dumps(users_description, ensure_ascii=False)
        ])
        
        logger.info(f"✅ Описание таблицы users добавлено в database_descriptions")
        logger.info(f"   Database: {database_name}")
        logger.info(f"   Schema: {schema_name}")
        logger.info(f"   Table: users")
        logger.info(f"   Type: table")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при добавлении описания: {str(e)}")
        return False

async def main():
    """Основная функция"""
    logger.info("🚀 Добавление описания таблицы users")
    logger.info("=" * 40)
    
    # Инициализируем подключение к базе данных
    try:
        await app_database_service.initialize()
        logger.info("✅ Подключение к базе данных установлено")
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к базе данных: {str(e)}")
        return
    
    # Добавляем описание для test1.demo1.users
    success = await add_users_table_description(
        database_name="test1",
        schema_name="demo1"
    )
    
    if success:
        logger.info("✅ Описание таблицы users успешно добавлено!")
    else:
        logger.info("❌ Не удалось добавить описание таблицы users")
    
    # Закрываем подключение
    await app_database_service.close()
    logger.info("🔚 Операция завершена")

if __name__ == "__main__":
    asyncio.run(main())
