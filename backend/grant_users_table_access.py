#!/usr/bin/env python3
"""
Скрипт для предоставления доступа к таблице users пользователю.
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

async def grant_users_table_access(role_name: str, database_name: str, schema_name: str = "public"):
    """Предоставляет доступ к таблице users для роли"""
    logger.info(f"🔐 Предоставление доступа к таблице users для роли {role_name}")
    
    try:
        # 1. Проверяем, существует ли уже такое право
        check_query = """
        SELECT id, permission_type, created_at
        FROM user_permissions 
        WHERE role_name = $1 
        AND database_name = $2 
        AND schema_name = $3
        AND table_name = 'users'
        """
        
        check_result = await app_database_service.execute_query(check_query, [role_name, database_name, schema_name])
        
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
        
        await app_database_service.execute_query(insert_query, [role_name, database_name, schema_name, 'users', 'SELECT'])
        
        logger.info(f"✅ Право доступа к таблице users предоставлено роли {role_name}")
        logger.info(f"   Database: {database_name}")
        logger.info(f"   Schema: {schema_name}")
        logger.info(f"   Permission: SELECT")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при предоставлении доступа: {str(e)}")
        return False

async def main():
    """Основная функция"""
    logger.info("🚀 Предоставление доступа к таблице users")
    logger.info("=" * 50)
    
    # Инициализируем подключение к базе данных
    try:
        await app_database_service.initialize()
        logger.info("✅ Подключение к базе данных установлено")
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к базе данных: {str(e)}")
        return
    
    # Предоставляем доступ для user_kirill
    success = await grant_users_table_access(
        role_name="user_kirill",
        database_name="test1", 
        schema_name="demo1"
    )
    
    if success:
        logger.info("✅ Доступ к таблице users успешно предоставлен!")
    else:
        logger.info("❌ Не удалось предоставить доступ к таблице users")
    
    # Закрываем подключение
    await app_database_service.close()
    logger.info("🔚 Операция завершена")

if __name__ == "__main__":
    asyncio.run(main())
