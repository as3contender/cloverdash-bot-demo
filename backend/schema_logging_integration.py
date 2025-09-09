#!/usr/bin/env python3
"""
Интеграционный модуль для добавления логирования схем в существующие API endpoints.

Этот модуль добавляет логирование schema_name и доступных таблиц в:
- /api/database/tables endpoint
- /api/database/table/{table_name}/sample endpoint
- LLM service при генерации SQL запросов
"""

import logging
from typing import Dict, List, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)

# Импортируем наш мониторинг схем
from schema_monitoring import schema_monitor, log_schema_access, log_table_access_endpoint


def enhance_database_api_logging():
    """
    Улучшает логирование в API endpoints базы данных
    """
    
    # Патчим существующий endpoint get_available_tables
    def patch_get_available_tables():
        """Добавляет детальное логирование в get_available_tables"""
        try:
            from api.database import get_available_tables as original_get_available_tables
            
            @wraps(original_get_available_tables)
            async def enhanced_get_available_tables(user_id: str = None):
                logger.info(f"🔍 API: Запрос доступных таблиц от пользователя {user_id}")
                
                try:
                    # Вызываем оригинальную функцию
                    result = await original_get_available_tables(user_id)
                    
                    # Добавляем детальное логирование
                    if isinstance(result, dict) and "tables" in result:
                        tables = result["tables"]
                        database_name = result.get("database_name", "unknown")
                        
                        # Группируем таблицы по схемам
                        schemas = {}
                        for table in tables:
                            schema_name = table.get("schema_name", "public")
                            if schema_name not in schemas:
                                schemas[schema_name] = []
                            schemas[schema_name].append(table.get("table_name", "unknown"))
                        
                        # Логируем информацию о схемах
                        logger.info(f"📊 API: Пользователь {user_id} имеет доступ к {len(schemas)} схемам")
                        for schema_name, table_names in schemas.items():
                            logger.info(f"   📂 Схема '{schema_name}': {len(table_names)} таблиц")
                            logger.debug(f"      📋 Таблицы: {', '.join(table_names)}")
                        
                        # Логируем доступ к каждой схеме
                        for schema_name, table_names in schemas.items():
                            for table_name in table_names:
                                schema_monitor.log_schema_access(
                                    user_id=user_id,
                                    schema_name=schema_name,
                                    table_name=table_name,
                                    access_type="list",
                                    success=True
                                )
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"❌ API: Ошибка при получении таблиц для пользователя {user_id}: {str(e)}")
                    raise
            
            # Заменяем оригинальную функцию
            import api.database
            api.database.get_available_tables = enhanced_get_available_tables
            logger.info("✅ Патч применен: get_available_tables")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при применении патча get_available_tables: {str(e)}")
    
    # Патчим endpoint get_table_sample
    def patch_get_table_sample():
        """Добавляет детальное логирование в get_table_sample"""
        try:
            from api.database import get_table_sample as original_get_table_sample
            
            @wraps(original_get_table_sample)
            async def enhanced_get_table_sample(
                table_name: str, 
                user_id: str = None, 
                limit: int = 5
            ):
                logger.info(f"🔍 API: Запрос образца данных таблицы {table_name} от пользователя {user_id}")
                
                # Извлекаем schema_name из table_name если есть
                schema_name = "public"  # по умолчанию
                if "." in table_name:
                    parts = table_name.split(".")
                    if len(parts) == 2:
                        schema_name, table_name = parts
                
                logger.info(f"📊 API: Схема: {schema_name}, Таблица: {table_name}")
                
                try:
                    # Вызываем оригинальную функцию
                    result = await original_get_table_sample(table_name, user_id, limit)
                    
                    # Логируем успешный доступ
                    schema_monitor.log_schema_access(
                        user_id=user_id,
                        schema_name=schema_name,
                        table_name=table_name,
                        access_type="sample",
                        success=True
                    )
                    
                    logger.info(f"✅ API: Успешно получен образец данных из {schema_name}.{table_name}")
                    return result
                    
                except Exception as e:
                    # Логируем неудачный доступ
                    schema_monitor.log_schema_access(
                        user_id=user_id,
                        schema_name=schema_name,
                        table_name=table_name,
                        access_type="sample",
                        success=False
                    )
                    
                    schema_monitor.log_schema_validation_error(
                        user_id=user_id,
                        schema_name=schema_name,
                        error_message=str(e)
                    )
                    
                    logger.error(f"❌ API: Ошибка при получении образца из {schema_name}.{table_name}: {str(e)}")
                    raise
            
            # Заменяем оригинальную функцию
            import api.database
            api.database.get_table_sample = enhanced_get_table_sample
            logger.info("✅ Патч применен: get_table_sample")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при применении патча get_table_sample: {str(e)}")
    
    # Применяем патчи
    patch_get_available_tables()
    patch_get_table_sample()


def enhance_llm_service_logging():
    """
    Улучшает логирование в LLM сервисе при генерации SQL запросов
    """
    
    def patch_llm_service():
        """Добавляет логирование схем в LLM сервис"""
        try:
            from services.llm_service import LLMService
            
            # Сохраняем оригинальный метод
            original_create_sql_prompt = LLMService._create_sql_prompt_with_user_permissions
            
            def enhanced_create_sql_prompt(self, natural_query: str, user_id: str, user_language: str = "en"):
                logger.info(f"🤖 LLM: Генерация SQL для пользователя {user_id}")
                logger.info(f"📝 LLM: Запрос: {natural_query}")
                
                try:
                    # Вызываем оригинальный метод
                    result = original_create_sql_prompt(self, natural_query, user_id, user_language)
                    
                    # Логируем информацию о схеме из промпта
                    if "demo1" in result:
                        logger.info(f"📊 LLM: Используется схема 'demo1' для пользователя {user_id}")
                        schema_monitor.log_schema_access(
                            user_id=user_id,
                            schema_name="demo1",
                            table_name="bills_view",
                            access_type="llm_generation",
                            success=True
                        )
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"❌ LLM: Ошибка при генерации SQL для пользователя {user_id}: {str(e)}")
                    raise
            
            # Заменяем метод
            LLMService._create_sql_prompt_with_user_permissions = enhanced_create_sql_prompt
            logger.info("✅ Патч применен: LLMService._create_sql_prompt_with_user_permissions")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при применении патча LLM сервиса: {str(e)}")


def enhance_app_database_logging():
    """
    Улучшает логирование в AppDatabaseService
    """
    
    def patch_get_user_accessible_tables():
        """Добавляет детальное логирование в get_user_accessible_tables"""
        try:
            from services.app_database import AppDatabaseService
            
            # Сохраняем оригинальный метод
            original_get_user_accessible_tables = AppDatabaseService.get_user_accessible_tables
            
            async def enhanced_get_user_accessible_tables(self, user_id: str, database_name: str):
                logger.info(f"🗄️  DB: Получение доступных таблиц для пользователя {user_id} в БД {database_name}")
                
                try:
                    # Вызываем оригинальный метод
                    result = await original_get_user_accessible_tables(self, user_id, database_name)
                    
                    # Анализируем результат
                    if result:
                        schemas = {}
                        for table in result:
                            schema_name = table.get("schema_name", "public")
                            if schema_name not in schemas:
                                schemas[schema_name] = []
                            schemas[schema_name].append(table.get("table_name", "unknown"))
                        
                        logger.info(f"📊 DB: Найдено {len(schemas)} схем для пользователя {user_id}")
                        for schema_name, table_names in schemas.items():
                            logger.info(f"   📂 Схема '{schema_name}': {len(table_names)} таблиц")
                            
                            # Логируем доступ к каждой таблице в схеме
                            for table_name in table_names:
                                schema_monitor.log_schema_access(
                                    user_id=user_id,
                                    schema_name=schema_name,
                                    table_name=table_name,
                                    access_type="permission_check",
                                    success=True
                                )
                    else:
                        logger.warning(f"⚠️  DB: Пользователь {user_id} не имеет доступа ни к одной таблице")
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"❌ DB: Ошибка при получении доступных таблиц для пользователя {user_id}: {str(e)}")
                    raise
            
            # Заменяем метод
            AppDatabaseService.get_user_accessible_tables = enhanced_get_user_accessible_tables
            logger.info("✅ Патч применен: AppDatabaseService.get_user_accessible_tables")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при применении патча AppDatabaseService: {str(e)}")


def initialize_schema_logging():
    """
    Инициализирует все улучшения логирования схем
    """
    logger.info("🚀 Инициализация логирования схем")
    
    try:
        # Применяем все патчи
        enhance_database_api_logging()
        enhance_llm_service_logging()
        enhance_app_database_logging()
        
        logger.info("✅ Все патчи логирования схем применены успешно")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при инициализации логирования схем: {str(e)}")


# Функция для создания отчета о схемах
async def generate_schema_report(user_id: str = None, database_name: str = None) -> Dict[str, Any]:
    """
    Генерирует отчет о схемах и доступных таблицах
    
    Args:
        user_id: ID пользователя (опционально)
        database_name: Имя базы данных (опционально)
    
    Returns:
        Dict с отчетом о схемах
    """
    logger.info("📊 Генерация отчета о схемах")
    
    try:
        from services.app_database import app_database_service
        from services.data_database import data_database_service
        
        if not database_name:
            database_name = data_database_service.get_database_name()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "database_name": database_name,
            "user_specific": user_id is not None,
            "user_id": user_id,
            "schemas": {},
            "summary": {}
        }
        
        if user_id:
            # Отчет для конкретного пользователя
            accessible_tables = await app_database_service.get_user_accessible_tables(
                user_id=user_id, 
                database_name=database_name
            )
            
            # Группируем по схемам
            schemas = {}
            for table in accessible_tables:
                schema_name = table.get("schema_name", "public")
                if schema_name not in schemas:
                    schemas[schema_name] = []
                schemas[schema_name].append({
                    "table_name": table.get("table_name"),
                    "object_type": table.get("object_type", "table"),
                    "description": table.get("description", "")
                })
            
            report["schemas"] = schemas
            report["summary"] = {
                "total_schemas": len(schemas),
                "total_tables": len(accessible_tables),
                "schemas_list": list(schemas.keys())
            }
            
        else:
            # Общий отчет по всем схемам
            all_descriptions = await app_database_service.get_all_table_descriptions(
                database_name=database_name
            )
            
            schemas = {}
            for key, description in all_descriptions.items():
                # key format: "database.schema.table"
                parts = key.split(".")
                if len(parts) >= 3:
                    schema_name = parts[-2]
                    table_name = parts[-1]
                    
                    if schema_name not in schemas:
                        schemas[schema_name] = []
                    
                    schemas[schema_name].append({
                        "table_name": table_name,
                        "object_type": description.get("object_type", "table"),
                        "description": description.get("description", "")
                    })
            
            report["schemas"] = schemas
            report["summary"] = {
                "total_schemas": len(schemas),
                "total_tables": len(all_descriptions),
                "schemas_list": list(schemas.keys())
            }
        
        # Логируем отчет
        logger.info(f"📋 Отчет сгенерирован: {report['summary']}")
        
        return report
        
    except Exception as e:
        logger.error(f"❌ Ошибка при генерации отчета о схемах: {str(e)}")
        return {"error": str(e)}


# Автоматическая инициализация при импорте модуля
if __name__ != "__main__":
    # Инициализируем логирование только если модуль импортируется
    try:
        initialize_schema_logging()
    except Exception as e:
        logger.error(f"❌ Ошибка при автоматической инициализации: {str(e)}")


if __name__ == "__main__":
    # Тестирование модуля
    import asyncio
    
    async def test_integration():
        """Тестирует интеграцию логирования"""
        logger.info("🧪 Тестирование интеграции логирования схем")
        
        # Инициализируем логирование
        initialize_schema_logging()
        
        # Генерируем тестовый отчет
        report = await generate_schema_report()
        logger.info(f"📊 Тестовый отчет: {report}")
        
        logger.info("✅ Тестирование завершено")
    
    asyncio.run(test_integration())

