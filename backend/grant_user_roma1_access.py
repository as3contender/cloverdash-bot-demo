#!/usr/bin/env python3
"""
Скрипт для предоставления доступа user_roma1 к таблице users.
"""

import asyncio
import logging
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.app_database import app_database_service

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def grant_user_roma1_access_to_users():
    """Предоставляет доступ user_roma1 к таблице users"""
    logger.info("🔐 Предоставление доступа user_roma1 к таблице users")
    
    try:
        # 1. Проверяем, существует ли уже такое право
        check_query = """
        SELECT id, permission_type, created_at
        FROM user_permissions 
        WHERE role_name = 'user_roma1' 
        AND database_name = 'cloverdash_bot' 
        AND schema_name = 'public'
        AND table_name = 'users'
        """
        
        check_result = await app_database_service.execute_query(check_query)
        
        if check_result.data:
            logger.info(f"✅ Право доступа уже существует:")
            for perm in check_result.data:
                logger.info(f"   Permission: {perm['permission_type']}")
                logger.info(f"   Created: {perm['created_at']}")
            return True
        
        # 2. Добавляем право доступа
        insert_query = """
        INSERT INTO user_permissions (role_name, database_name, schema_name, table_name, permission_type, created_at)
        VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
        """
        
        await app_database_service.execute_query(insert_query, [
            'user_roma1', 
            'cloverdash_bot', 
            'public', 
            'users', 
            'SELECT'
        ])
        
        logger.info(f"✅ Право доступа к таблице users предоставлено роли user_roma1")
        logger.info(f"   Database: cloverdash_bot")
        logger.info(f"   Schema: public")
        logger.info(f"   Permission: SELECT")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при предоставлении доступа: {str(e)}")
        return False

async def add_users_table_description_for_cloverdash_bot():
    """Добавляет описание таблицы users для базы cloverdash_bot"""
    logger.info("📝 Добавление описания таблицы users для cloverdash_bot")
    
    try:
        # Проверяем, существует ли уже описание
        check_query = """
        SELECT id, table_description, created_at
        FROM database_descriptions 
        WHERE database_name = 'cloverdash_bot' 
        AND schema_name = 'public' 
        AND table_name = 'users'
        """
        
        check_result = await app_database_service.execute_query(check_query)
        
        if check_result.data:
            logger.info(f"✅ Описание таблицы users уже существует для cloverdash_bot")
            return True
        
        # Создаем описание таблицы users
        import json
        users_description = {
            "description": "Таблица пользователей системы",
            "object_type": "table",
            "columns": {
                "id": {
                    "description": "Уникальный идентификатор пользователя",
                    "datatype": "uuid",
                    "type": "uuid",
                    "nullable": False,
                    "default": "gen_random_uuid()",
                    "primary_key": True
                },
                "username": {
                    "description": "Имя пользователя",
                    "datatype": "character varying",
                    "type": "character varying(100)",
                    "nullable": True,
                    "default": None,
                    "unique": True
                },
                "email": {
                    "description": "Email адрес пользователя",
                    "datatype": "character varying",
                    "type": "character varying(255)",
                    "nullable": True,
                    "default": None,
                    "unique": True
                },
                "full_name": {
                    "description": "Полное имя пользователя",
                    "datatype": "character varying",
                    "type": "character varying(255)",
                    "nullable": True,
                    "default": None
                },
                "hashed_password": {
                    "description": "Хэшированный пароль пользователя",
                    "datatype": "character varying",
                    "type": "character varying(255)",
                    "nullable": True,
                    "default": None
                },
                "telegram_id": {
                    "description": "Telegram ID пользователя",
                    "datatype": "character varying",
                    "type": "character varying(100)",
                    "nullable": True,
                    "default": None,
                    "unique": True
                },
                "telegram_username": {
                    "description": "Telegram username пользователя",
                    "datatype": "character varying",
                    "type": "character varying(100)",
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
                    "type": "timestamp",
                    "nullable": False,
                    "default": "CURRENT_TIMESTAMP"
                },
                "updated_at": {
                    "description": "Дата последнего обновления записи",
                    "datatype": "timestamp without time zone",
                    "type": "timestamp",
                    "nullable": False,
                    "default": "CURRENT_TIMESTAMP"
                }
            }
        }
        
        # Добавляем описание в database_descriptions
        insert_query = """
        INSERT INTO database_descriptions (database_name, schema_name, table_name, object_type, table_description, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """
        
        await app_database_service.execute_query(insert_query, [
            'cloverdash_bot', 
            'public', 
            'users', 
            'table', 
            json.dumps(users_description, ensure_ascii=False)
        ])
        
        logger.info(f"✅ Описание таблицы users добавлено для cloverdash_bot")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при добавлении описания: {str(e)}")
        return False

async def main():
    """Основная функция"""
    logger.info("🚀 Предоставление доступа user_roma1 к таблице users")
    logger.info("=" * 60)
    
    # Инициализируем подключение к базе данных
    try:
        await app_database_service.initialize()
        logger.info("✅ Подключение к базе данных установлено")
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к базе данных: {str(e)}")
        return
    
    # 1. Добавляем описание таблицы users для cloverdash_bot
    desc_success = await add_users_table_description_for_cloverdash_bot()
    
    # 2. Предоставляем доступ user_roma1 к таблице users
    access_success = await grant_user_roma1_access_to_users()
    
    if desc_success and access_success:
        logger.info("✅ Доступ user_roma1 к таблице users успешно настроен!")
    else:
        logger.info("❌ Не удалось полностью настроить доступ")
    
    # Закрываем подключение
    await app_database_service.close()
    logger.info("🔚 Операция завершена")

if __name__ == "__main__":
    asyncio.run(main())

