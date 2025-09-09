#!/usr/bin/env python3
"""
Скрипт для создания роли user_kirill в базе данных пользовательских данных.

Этот скрипт подключается напрямую к базе данных и создает роль с необходимыми правами.
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
        logging.FileHandler('create_user_kirill_role.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def create_user_kirill_role():
    """Создает роль user_kirill в базе данных пользовательских данных"""
    logger.info("🔧 Создание роли user_kirill в базе данных пользовательских данных")
    
    connection = None
    
    try:
        from config.settings import settings
        
        # Подключаемся напрямую к базе данных пользовательских данных
        logger.info("🔌 Подключение к базе данных пользовательских данных...")
        connection = await asyncpg.connect(settings.data_database_url)
        logger.info("✅ Подключение установлено")
        
        # 1. Проверяем, существует ли роль
        logger.info("🔍 Проверка существования роли user_kirill...")
        
        check_query = "SELECT rolname FROM pg_roles WHERE rolname = 'user_kirill'"
        result = await connection.fetch(check_query)
        
        if result:
            logger.info("ℹ️  Роль user_kirill уже существует")
        else:
            logger.info("❌ Роль user_kirill не существует, создаем...")
            
            # 2. Создаем роль
            create_role_query = "CREATE ROLE user_kirill"
            await connection.execute(create_role_query)
            logger.info("✅ Роль user_kirill создана")
        
        # 3. Предоставляем права на схему public
        logger.info("🔐 Предоставление прав на схему public...")
        
        try:
            grant_public_query = "GRANT USAGE ON SCHEMA public TO user_kirill"
            await connection.execute(grant_public_query)
            logger.info("✅ Предоставлены права на схему public")
        except Exception as e:
            logger.warning(f"⚠️  Не удалось предоставить права на схему public: {str(e)}")
        
        # 4. Предоставляем права на схему demo1
        logger.info("🔐 Предоставление прав на схему demo1...")
        
        try:
            grant_demo1_query = "GRANT USAGE ON SCHEMA demo1 TO user_kirill"
            await connection.execute(grant_demo1_query)
            logger.info("✅ Предоставлены права на схему demo1")
        except Exception as e:
            logger.warning(f"⚠️  Не удалось предоставить права на схему demo1: {str(e)}")
        
        # 5. Предоставляем права на bills_view (из user_permissions)
        logger.info("🔐 Предоставление прав на bills_view...")
        
        try:
            grant_bills_view_query = "GRANT SELECT ON demo1.bills_view TO user_kirill"
            await connection.execute(grant_bills_view_query)
            logger.info("✅ Предоставлены права SELECT на demo1.bills_view")
        except Exception as e:
            logger.warning(f"⚠️  Не удалось предоставить права на bills_view: {str(e)}")
        
        # 6. Проверяем созданную роль
        logger.info("🔍 Проверка созданной роли...")
        
        check_role_query = """
        SELECT rolname, rolsuper, rolinherit, rolcreaterole, rolcreatedb, rolcanlogin
        FROM pg_roles 
        WHERE rolname = 'user_kirill'
        """
        result = await connection.fetch(check_role_query)
        
        if result:
            role_info = result[0]
            logger.info("✅ Роль user_kirill успешно создана:")
            logger.info(f"   • Имя: {role_info['rolname']}")
            logger.info(f"   • Superuser: {role_info['rolsuper']}")
            logger.info(f"   • Can login: {role_info['rolcanlogin']}")
            logger.info(f"   • Create role: {role_info['rolcreaterole']}")
            logger.info(f"   • Create DB: {role_info['rolcreatedb']}")
        else:
            logger.error("❌ Роль user_kirill не найдена после создания")
            return False
        
        # 7. Проверяем права на bills_view
        logger.info("🔍 Проверка прав на bills_view...")
        
        try:
            test_query = "SELECT COUNT(*) FROM demo1.bills_view"
            result = await connection.fetch(test_query)
            logger.info(f"✅ Тестовый запрос к bills_view выполнен: {result[0]['count']} строк")
        except Exception as e:
            logger.warning(f"⚠️  Не удалось выполнить тестовый запрос к bills_view: {str(e)}")
        
        logger.info("🎉 Создание роли user_kirill завершено успешно!")
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
    logger.info("🚀 Создание роли user_kirill")
    logger.info(f"⏰ Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    try:
        success = await create_user_kirill_role()
        
        if success:
            logger.info("🎯 Создание роли завершено успешно!")
            return 0
        else:
            logger.error("💥 Создание роли завершено с ошибками!")
            return 1
            
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

