import asyncio
from services.app_database import app_database_service

async def check_descriptions():
    try:
        await app_database_service.initialize()
        
        # Проверяем ВСЕ описания таблиц
        result = await app_database_service.execute_query("""
            SELECT database_name, schema_name, table_name, object_type
            FROM database_descriptions 
            ORDER BY database_name, schema_name, table_name
        """)
        
        print('=== ВСЕ ТАБЛИЦЫ В DATABASE_DESCRIPTIONS ===')
        for desc in result.data:
            print(f'{desc["database_name"]}.{desc["schema_name"]}.{desc["table_name"]} ({desc["object_type"]})')
            
    except Exception as e:
        print(f'Ошибка: {e}')

if __name__ == "__main__":
    asyncio.run(check_descriptions())
