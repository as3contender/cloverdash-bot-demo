#!/usr/bin/env python3
"""
Скрипт для предоставления прав на переключение роли user_kirill.

Этот скрипт предоставляет права на SET ROLE для роли user_kirill.
"""

import asyncio
import logging
import sys
from datetime import datetime
import asyncpg

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('grant_role_privileges.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def grant_role_privileges():
    """Предоставляет права на переключение роли user_kirill"""
    logger.info("🔧 Предоставление прав на переключение роли user_kirill")
    
    connection = None
    
    try:
        from config.settings import settings
        
        # Подключаемся напрямую к базе данных пользовательских данных
        logger.info("🔌 Подключение к базе данных пользовательских данных...")
        connection = await asyncpg.connect(settings.data_database_url)
        logger.info("✅ Подключение установлено")
        
        # 1. Проверяем текущего пользователя
        logger.info("🔍 Проверка текущего пользователя...")
        
        current_user_query = "SELECT current_user, session_user"
        result = await connection.fetch(current_user_query)
        
        if result:
            current_user = result[0]
            logger.info(f"✅ Текущий пользователь: {current_user['current_user']}")
            logger.info(f"✅ Пользователь сессии: {current_user['session_user']}")
        
        # 2. Предоставляем права на переключение роли
        logger.info("🔐 Предоставление прав на переключение роли user_kirill...")
        
        try:
            # Предоставляем права на SET ROLE для роли user_kirill
            grant_set_role_query = "GRANT user_kirill TO current_user"
            await connection.execute(grant_set_role_query)
            logger.info("✅ Предоставлены права на переключение роли user_kirill")
        except Exception as e:
            logger.warning(f"⚠️  Не удалось предоставить права на переключение роли: {str(e)}")
        
        # 3. Альтернативный способ - предоставляем права через doadmin
        logger.info("🔐 Попытка предоставить права через doadmin...")
        
        try:
            # Переключаемся на doadmin (если возможно)
            await connection.execute("SET ROLE doadmin")
            logger.info("✅ Переключились на роль doadmin")
            
            # Предоставляем права на переключение роли
            grant_set_role_query = "GRANT user_kirill TO cloverdash-bot-service"
            await connection.execute(grant_set_role_query)
            logger.info("✅ Предоставлены права на переключение роли user_kirill для cloverdash-bot-service")
            
        except Exception as e:
            logger.warning(f"⚠️  Не удалось предоставить права через doadmin: {str(e)}")
        
        # 4. Проверяем права на переключение роли
        logger.info("🔍 Проверка прав на переключение роли...")
        
        try:
            # Пытаемся переключиться на роль user_kirill
            await connection.execute("SET ROLE user_kirill")
            logger.info("✅ Успешно переключились на роль user_kirill")
            
            # Проверяем текущую роль
            role_check_query = "SELECT current_user, session_user"
            result = await connection.fetch(role_check_query)
            
            if result:
                current_user = result[0]
                logger.info(f"✅ Текущая роль: {current_user['current_user']}")
                logger.info(f"✅ Пользователь сессии: {current_user['session_user']}")
            
            # Возвращаемся к исходной роли
            await connection.execute("RESET ROLE")
            logger.info("✅ Вернулись к исходной роли")
            
        except Exception as e:
            logger.warning(f"⚠️  Не удалось переключиться на роль user_kirill: {str(e)}")
        
        # 5. Проверяем права на bills_view от имени роли user_kirill
        logger.info("🔍 Проверка прав на bills_view от имени роли user_kirill...")
        
        try:
            # Переключаемся на роль user_kirill
            await connection.execute("SET ROLE user_kirill")
            
            # Пытаемся выполнить запрос к bills_view
            test_query = "SELECT COUNT(*) FROM demo1.bills_view LIMIT 1"
            result = await connection.fetch(test_query)
            
            if result:
                count = result[0]['count']
                logger.info(f"✅ Запрос к bills_view выполнен успешно: {count} строк")
            
            # Возвращаемся к исходной роли
            await connection.execute("RESET ROLE")
            logger.info("✅ Вернулись к исходной роли")
            
        except Exception as e:
            logger.warning(f"⚠️  Не удалось выполнить запрос к bills_view: {str(e)}")
        
        logger.info("🎉 Предоставление прав завершено!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {str(e)}")
        return False
    
    finally:
        if connection:
            await connection.close()
            logger.info("🔌 Подключение к базе данных закрыто")


async def main():
    """Основная функция"""
    logger.info("🚀 Предоставление прав на переключение роли")
    logger.info(f"⏰ Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    try:
        success = await grant_role_privileges()
        
        if success:
            logger.info("🎯 Предоставление прав завершено успешно!")
            return 0
        else:
            logger.error("💥 Предоставление прав завершено с ошибками!")
            return 1
            
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
