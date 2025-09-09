#!/usr/bin/env python3
"""
Модуль для мониторинга и логирования схем базы данных.

Интегрируется с существующей системой логирования для отслеживания:
- Доступности схем для пользователей
- Изменений в правах доступа к схемам
- Проблем с schema_name в запросах
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)

class SchemaMonitor:
    """Класс для мониторинга схем базы данных"""
    
    def __init__(self):
        self.schema_cache = {}
        self.user_access_cache = {}
        self.last_check = None
    
    def log_schema_access(self, user_id: str, schema_name: str, table_name: str, 
                         access_type: str = "read", success: bool = True):
        """
        Логирует доступ пользователя к схеме
        
        Args:
            user_id: ID пользователя
            schema_name: Имя схемы
            table_name: Имя таблицы
            access_type: Тип доступа (read, write, execute)
            success: Успешность доступа
        """
        timestamp = datetime.now()
        status = "✅" if success else "❌"
        
        logger.info(
            f"{status} СХЕМА: Пользователь {user_id} | "
            f"Схема: {schema_name} | Таблица: {table_name} | "
            f"Тип: {access_type} | Время: {timestamp.strftime('%H:%M:%S')}"
        )
        
        # Кэшируем информацию о доступе
        cache_key = f"{user_id}:{schema_name}"
        if cache_key not in self.user_access_cache:
            self.user_access_cache[cache_key] = {
                "last_access": timestamp,
                "access_count": 0,
                "tables_accessed": set(),
                "failed_attempts": 0
            }
        
        cache_entry = self.user_access_cache[cache_key]
        cache_entry["last_access"] = timestamp
        cache_entry["tables_accessed"].add(table_name)
        
        if success:
            cache_entry["access_count"] += 1
        else:
            cache_entry["failed_attempts"] += 1
            logger.warning(
                f"⚠️  НЕУДАЧНЫЙ ДОСТУП: Пользователь {user_id} не смог получить доступ "
                f"к таблице {schema_name}.{table_name}"
            )
    
    def log_schema_validation_error(self, user_id: str, schema_name: str, 
                                   error_message: str, query: str = None):
        """
        Логирует ошибки валидации схемы
        
        Args:
            user_id: ID пользователя
            schema_name: Имя схемы
            error_message: Сообщение об ошибке
            query: SQL запрос (если есть)
        """
        logger.error(
            f"❌ ОШИБКА СХЕМЫ: Пользователь {user_id} | "
            f"Схема: {schema_name} | Ошибка: {error_message}"
        )
        
        if query:
            logger.debug(f"🔍 Проблемный запрос: {query}")
    
    def log_schema_not_found(self, user_id: str, schema_name: str, 
                           available_schemas: List[str] = None):
        """
        Логирует случаи, когда схема не найдена
        
        Args:
            user_id: ID пользователя
            schema_name: Запрашиваемая схема
            available_schemas: Список доступных схем
        """
        logger.warning(
            f"⚠️  СХЕМА НЕ НАЙДЕНА: Пользователь {user_id} | "
            f"Запрашиваемая схема: {schema_name}"
        )
        
        if available_schemas:
            logger.info(f"📋 Доступные схемы: {', '.join(available_schemas)}")
    
    def get_user_schema_stats(self, user_id: str) -> Dict[str, Any]:
        """Возвращает статистику доступа пользователя к схемам"""
        user_stats = {
            "user_id": user_id,
            "schemas_accessed": [],
            "total_access_count": 0,
            "total_failed_attempts": 0,
            "last_activity": None
        }
        
        for cache_key, cache_data in self.user_access_cache.items():
            if cache_key.startswith(f"{user_id}:"):
                schema_name = cache_key.split(":", 1)[1]
                user_stats["schemas_accessed"].append({
                    "schema_name": schema_name,
                    "access_count": cache_data["access_count"],
                    "failed_attempts": cache_data["failed_attempts"],
                    "tables_accessed": list(cache_data["tables_accessed"]),
                    "last_access": cache_data["last_access"].isoformat()
                })
                user_stats["total_access_count"] += cache_data["access_count"]
                user_stats["total_failed_attempts"] += cache_data["failed_attempts"]
                
                if (user_stats["last_activity"] is None or 
                    cache_data["last_access"] > datetime.fromisoformat(user_stats["last_activity"])):
                    user_stats["last_activity"] = cache_data["last_access"].isoformat()
        
        return user_stats
    
    def log_daily_schema_report(self):
        """Генерирует ежедневный отчет по схемам"""
        logger.info("=" * 80)
        logger.info("📊 ЕЖЕДНЕВНЫЙ ОТЧЕТ ПО СХЕМАМ")
        logger.info(f"📅 Дата: {datetime.now().strftime('%Y-%m-%d')}")
        logger.info("=" * 80)
        
        # Статистика по пользователям
        unique_users = set()
        total_accesses = 0
        total_failures = 0
        
        for cache_key, cache_data in self.user_access_cache.items():
            user_id = cache_key.split(":", 1)[0]
            unique_users.add(user_id)
            total_accesses += cache_data["access_count"]
            total_failures += cache_data["failed_attempts"]
        
        logger.info(f"👥 Уникальных пользователей: {len(unique_users)}")
        logger.info(f"✅ Всего успешных обращений: {total_accesses}")
        logger.info(f"❌ Всего неудачных попыток: {total_failures}")
        
        if total_accesses > 0:
            success_rate = ((total_accesses - total_failures) / total_accesses) * 100
            logger.info(f"📈 Процент успешности: {success_rate:.1f}%")
        
        # Топ схем по использованию
        schema_usage = {}
        for cache_key, cache_data in self.user_access_cache.items():
            schema_name = cache_key.split(":", 1)[1]
            if schema_name not in schema_usage:
                schema_usage[schema_name] = 0
            schema_usage[schema_name] += cache_data["access_count"]
        
        if schema_usage:
            sorted_schemas = sorted(schema_usage.items(), key=lambda x: x[1], reverse=True)
            logger.info("🏆 Топ схем по использованию:")
            for schema_name, count in sorted_schemas[:5]:
                logger.info(f"   • {schema_name}: {count} обращений")
        
        logger.info("=" * 80)


# Декоратор для автоматического логирования доступа к схемам
def log_schema_access(schema_name_param: str = "schema_name", 
                     table_name_param: str = "table_name"):
    """
    Декоратор для автоматического логирования доступа к схемам
    
    Args:
        schema_name_param: Имя параметра, содержащего schema_name
        table_name_param: Имя параметра, содержащего table_name
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Извлекаем параметры из kwargs
            schema_name = kwargs.get(schema_name_param, "unknown")
            table_name = kwargs.get(table_name_param, "unknown")
            user_id = kwargs.get("user_id", "unknown")
            
            # Логируем начало доступа
            logger.debug(f"🔍 Попытка доступа к схеме {schema_name}.{table_name} пользователем {user_id}")
            
            try:
                result = await func(*args, **kwargs)
                # Логируем успешный доступ
                schema_monitor.log_schema_access(
                    user_id=user_id,
                    schema_name=schema_name,
                    table_name=table_name,
                    access_type="read",
                    success=True
                )
                return result
            except Exception as e:
                # Логируем неудачный доступ
                schema_monitor.log_schema_access(
                    user_id=user_id,
                    schema_name=schema_name,
                    table_name=table_name,
                    access_type="read",
                    success=False
                )
                schema_monitor.log_schema_validation_error(
                    user_id=user_id,
                    schema_name=schema_name,
                    error_message=str(e)
                )
                raise
        return wrapper
    return decorator


# Глобальный экземпляр монитора
schema_monitor = SchemaMonitor()


# Функция для интеграции с существующими API endpoints
async def log_table_access_endpoint(user_id: str, database_name: str, 
                                  schema_name: str = None, table_name: str = None):
    """
    Функция для логирования доступа к таблицам через API endpoints
    
    Args:
        user_id: ID пользователя
        database_name: Имя базы данных
        schema_name: Имя схемы (опционально)
        table_name: Имя таблицы (опционально)
    """
    try:
        from services.app_database import app_database_service
        
        # Получаем доступные таблицы для пользователя
        accessible_tables = await app_database_service.get_user_accessible_tables(
            user_id=user_id, 
            database_name=database_name
        )
        
        # Группируем по схемам
        schemas = {}
        for table in accessible_tables:
            table_schema = table.get("schema_name", "public")
            if table_schema not in schemas:
                schemas[table_schema] = []
            schemas[table_schema].append(table["table_name"])
        
        # Логируем информацию о доступных схемах
        logger.info(f"📋 Пользователь {user_id} имеет доступ к схемам: {list(schemas.keys())}")
        
        # Если указана конкретная схема, проверяем доступ
        if schema_name:
            if schema_name in schemas:
                logger.info(f"✅ Пользователь {user_id} имеет доступ к схеме {schema_name}")
                if table_name and table_name in schemas[schema_name]:
                    logger.info(f"✅ Пользователь {user_id} имеет доступ к таблице {schema_name}.{table_name}")
                    schema_monitor.log_schema_access(user_id, schema_name, table_name, "read", True)
                elif table_name:
                    logger.warning(f"⚠️  Пользователь {user_id} НЕ имеет доступа к таблице {schema_name}.{table_name}")
                    schema_monitor.log_schema_access(user_id, schema_name, table_name, "read", False)
            else:
                logger.warning(f"⚠️  Пользователь {user_id} НЕ имеет доступа к схеме {schema_name}")
                schema_monitor.log_schema_not_found(user_id, schema_name, list(schemas.keys()))
        
        return {
            "user_id": user_id,
            "database_name": database_name,
            "accessible_schemas": list(schemas.keys()),
            "schemas_details": schemas
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка при логировании доступа к таблицам: {str(e)}")
        if schema_name:
            schema_monitor.log_schema_validation_error(user_id, schema_name, str(e))
        raise


# Функция для периодического мониторинга
async def start_schema_monitoring():
    """Запускает периодический мониторинг схем"""
    logger.info("🔄 Запуск периодического мониторинга схем")
    
    while True:
        try:
            # Генерируем ежедневный отчет
            schema_monitor.log_daily_schema_report()
            
            # Ждем до следующего дня
            await asyncio.sleep(24 * 60 * 60)  # 24 часа
            
        except Exception as e:
            logger.error(f"❌ Ошибка в периодическом мониторинге: {str(e)}")
            await asyncio.sleep(60)  # Ждем минуту перед повтором


if __name__ == "__main__":
    # Пример использования
    async def test_schema_monitoring():
        """Тестовая функция для демонстрации работы мониторинга"""
        logger.info("🧪 Тестирование мониторинга схем")
        
        # Симулируем доступы к схемам
        schema_monitor.log_schema_access("user1", "public", "users", "read", True)
        schema_monitor.log_schema_access("user1", "demo1", "bills_view", "read", True)
        schema_monitor.log_schema_access("user2", "public", "orders", "read", False)
        
        # Получаем статистику
        stats = schema_monitor.get_user_schema_stats("user1")
        logger.info(f"📊 Статистика пользователя user1: {stats}")
        
        # Генерируем отчет
        schema_monitor.log_daily_schema_report()
    
    asyncio.run(test_schema_monitoring())
