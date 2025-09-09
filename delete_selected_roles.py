#!/usr/bin/env python3
"""
Удаление выделенных ролей user_denis и denis_none из базы данных
"""

import asyncio
import asyncpg
import logging
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

async def delete_selected_roles():
    """
    Удаляет роли user_denis и denis_none из базы данных
    """
    logger.info("🗑️ УДАЛЕНИЕ ВЫДЕЛЕННЫХ РОЛЕЙ")
    logger.info("=" * 50)
    
    # Роли для удаления
    roles_to_delete = ['user_denis', 'denis_none']
    
    connection = None
    
    try:
        # Подключение к базе данных
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("❌ DATABASE_URL не найден в переменных окружения")
            return False
        
        logger.info("🔌 Подключение к базе данных...")
        connection = await asyncpg.connect(database_url)
        logger.info("✅ Подключение установлено")
        
        # Проверяем существование ролей перед удалением
        logger.info("🔍 Проверка существования ролей...")
        
        for role_name in roles_to_delete:
            check_query = "SELECT rolname FROM pg_roles WHERE rolname = $1"
            result = await connection.fetchrow(check_query, role_name)
            
            if result:
                logger.info(f"✅ Роль {role_name} найдена")
            else:
                logger.warning(f"⚠️ Роль {role_name} не найдена")
        
        # Удаляем роли
        logger.info("🗑️ Удаление ролей...")
        
        for role_name in roles_to_delete:
            try:
                # Сначала отзываем все права роли
                logger.info(f"🔄 Отзыв прав для роли {role_name}...")
                await connection.execute(f"REVOKE ALL ON ALL TABLES IN SCHEMA public FROM {role_name}")
                await connection.execute(f"REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM {role_name}")
                await connection.execute(f"REVOKE USAGE ON SCHEMA public FROM {role_name}")
                
                # Удаляем роль
                logger.info(f"🗑️ Удаление роли {role_name}...")
                await connection.execute(f"DROP ROLE IF EXISTS {role_name}")
                logger.info(f"✅ Роль {role_name} успешно удалена")
                
            except Exception as e:
                logger.error(f"❌ Ошибка при удалении роли {role_name}: {str(e)}")
        
        # Проверяем результат
        logger.info("🔍 Проверка результата...")
        
        for role_name in roles_to_delete:
            check_query = "SELECT rolname FROM pg_roles WHERE rolname = $1"
            result = await connection.fetchrow(check_query, role_name)
            
            if result:
                logger.error(f"❌ Роль {role_name} все еще существует")
            else:
                logger.info(f"✅ Роль {role_name} успешно удалена")
        
        logger.info("🎉 Удаление ролей завершено")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при удалении ролей: {str(e)}")
        return False
        
    finally:
        if connection:
            await connection.close()
            logger.info("🔌 Соединение закрыто")

if __name__ == "__main__":
    asyncio.run(delete_selected_roles())
