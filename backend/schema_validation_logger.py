#!/usr/bin/env python3
"""
Скрипт для логирования проверки schema_name с доступными для пользователя таблицами.

Этот скрипт проверяет и логирует:
1. Какие схемы доступны в базе данных
2. Какие таблицы доступны для каждого пользователя в каждой схеме
3. Соответствие между schema_name и фактически доступными таблицами
4. Проблемы с правами доступа к схемам
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('schema_validation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class SchemaValidationLogger:
    """Класс для логирования проверки схем и доступных таблиц"""
    
    def __init__(self):
        self.log_file = Path("schema_validation.log")
        self.validation_results = []
    
    async def validate_schema_access(self, user_id: str, database_name: str) -> Dict[str, Any]:
        """
        Проверяет доступ пользователя к схемам и таблицам
        
        Args:
            user_id: ID пользователя
            database_name: Имя базы данных
            
        Returns:
            Dict с результатами проверки
        """
        try:
            from services.app_database import app_database_service
            from services.data_database import data_database_service
            
            logger.info(f"🔍 Начинаем проверку схем для пользователя {user_id} в БД {database_name}")
            
            # Проверяем подключение к базам данных
            if not app_database_service.is_connected:
                logger.error("❌ База описаний недоступна")
                return {"error": "База описаний недоступна"}
            
            if not data_database_service.is_connected:
                logger.error("❌ База данных недоступна")
                return {"error": "База данных недоступна"}
            
            # Получаем доступные таблицы для пользователя
            accessible_tables = await app_database_service.get_user_accessible_tables(
                user_id=user_id, 
                database_name=database_name
            )
            
            logger.info(f"📊 Получено {len(accessible_tables)} доступных таблиц для пользователя {user_id}")
            
            # Группируем таблицы по схемам
            schemas_info = self._group_tables_by_schema(accessible_tables)
            
            # Получаем полную схему базы данных
            full_schema = await app_database_service.get_database_schema(
                database_name=database_name,
                include_views=True,
                schema_name=None  # Получаем все схемы
            )
            
            # Анализируем доступность схем
            schema_analysis = self._analyze_schema_access(schemas_info, full_schema, user_id)
            
            # Логируем результаты
            self._log_schema_validation_results(user_id, database_name, schema_analysis)
            
            return {
                "user_id": user_id,
                "database_name": database_name,
                "accessible_tables_count": len(accessible_tables),
                "schemas_info": schemas_info,
                "schema_analysis": schema_analysis,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке схем для пользователя {user_id}: {str(e)}")
            return {"error": str(e)}
    
    def _group_tables_by_schema(self, tables: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Группирует таблицы по схемам"""
        schemas = {}
        
        for table in tables:
            schema_name = table.get("schema_name", "public")
            if schema_name not in schemas:
                schemas[schema_name] = []
            schemas[schema_name].append(table)
        
        logger.info(f"📁 Найдено схем: {list(schemas.keys())}")
        for schema_name, tables_in_schema in schemas.items():
            logger.info(f"   📂 Схема '{schema_name}': {len(tables_in_schema)} таблиц")
        
        return schemas
    
    def _analyze_schema_access(self, user_schemas: Dict[str, List], full_schema: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Анализирует доступность схем для пользователя"""
        analysis = {
            "accessible_schemas": list(user_schemas.keys()),
            "schema_details": {},
            "issues": [],
            "recommendations": []
        }
        
        # Анализируем каждую доступную схему
        for schema_name, tables in user_schemas.items():
            schema_detail = {
                "tables_count": len(tables),
                "tables": [t["table_name"] for t in tables],
                "object_types": {}
            }
            
            # Подсчитываем типы объектов
            for table in tables:
                obj_type = table.get("object_type", "table")
                if obj_type not in schema_detail["object_types"]:
                    schema_detail["object_types"][obj_type] = 0
                schema_detail["object_types"][obj_type] += 1
            
            analysis["schema_details"][schema_name] = schema_detail
            
            logger.info(f"✅ Схема '{schema_name}' доступна для пользователя {user_id}")
            logger.info(f"   📊 Таблиц: {schema_detail['tables_count']}")
            logger.info(f"   📋 Типы объектов: {schema_detail['object_types']}")
        
        # Проверяем, есть ли схемы, к которым у пользователя нет доступа
        all_schemas_in_db = set()
        for table_name, table_info in full_schema.items():
            schema_name = table_info.get("schema_name", "public")
            all_schemas_in_db.add(schema_name)
        
        accessible_schemas = set(user_schemas.keys())
        restricted_schemas = all_schemas_in_db - accessible_schemas
        
        if restricted_schemas:
            analysis["issues"].append(f"Пользователь {user_id} не имеет доступа к схемам: {list(restricted_schemas)}")
            logger.warning(f"⚠️  Пользователь {user_id} не имеет доступа к схемам: {list(restricted_schemas)}")
        
        # Рекомендации
        if not user_schemas:
            analysis["recommendations"].append("Пользователь не имеет доступа ни к одной схеме")
            logger.warning(f"⚠️  Пользователь {user_id} не имеет доступа ни к одной схеме")
        elif len(user_schemas) == 1 and "public" in user_schemas:
            analysis["recommendations"].append("Пользователь имеет доступ только к схеме 'public'")
            logger.info(f"ℹ️  Пользователь {user_id} имеет доступ только к схеме 'public'")
        
        return analysis
    
    def _log_schema_validation_results(self, user_id: str, database_name: str, analysis: Dict[str, Any]):
        """Логирует результаты проверки схем"""
        logger.info("=" * 80)
        logger.info(f"📋 РЕЗУЛЬТАТЫ ПРОВЕРКИ СХЕМ ДЛЯ ПОЛЬЗОВАТЕЛЯ {user_id}")
        logger.info(f"🗄️  База данных: {database_name}")
        logger.info(f"⏰ Время проверки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)
        
        # Доступные схемы
        accessible_schemas = analysis.get("accessible_schemas", [])
        logger.info(f"✅ Доступные схемы ({len(accessible_schemas)}): {accessible_schemas}")
        
        # Детали по схемам
        schema_details = analysis.get("schema_details", {})
        for schema_name, details in schema_details.items():
            logger.info(f"📂 Схема '{schema_name}':")
            logger.info(f"   📊 Количество таблиц: {details['tables_count']}")
            logger.info(f"   📋 Типы объектов: {details['object_types']}")
            logger.info(f"   📝 Таблицы: {', '.join(details['tables'])}")
        
        # Проблемы
        issues = analysis.get("issues", [])
        if issues:
            logger.warning("⚠️  ПРОБЛЕМЫ:")
            for issue in issues:
                logger.warning(f"   • {issue}")
        else:
            logger.info("✅ Проблем не обнаружено")
        
        # Рекомендации
        recommendations = analysis.get("recommendations", [])
        if recommendations:
            logger.info("💡 РЕКОМЕНДАЦИИ:")
            for rec in recommendations:
                logger.info(f"   • {rec}")
        
        logger.info("=" * 80)
    
    async def validate_multiple_users(self, user_ids: List[str], database_name: str) -> Dict[str, Any]:
        """Проверяет доступ к схемам для нескольких пользователей"""
        logger.info(f"🔄 Начинаем проверку схем для {len(user_ids)} пользователей")
        
        results = {}
        for user_id in user_ids:
            logger.info(f"👤 Проверяем пользователя: {user_id}")
            result = await self.validate_schema_access(user_id, database_name)
            results[user_id] = result
        
        # Сводный отчет
        self._generate_summary_report(results, database_name)
        
        return results
    
    def _generate_summary_report(self, results: Dict[str, Any], database_name: str):
        """Генерирует сводный отчет по всем пользователям"""
        logger.info("=" * 100)
        logger.info("📊 СВОДНЫЙ ОТЧЕТ ПО ПРОВЕРКЕ СХЕМ")
        logger.info(f"🗄️  База данных: {database_name}")
        logger.info(f"👥 Количество пользователей: {len(results)}")
        logger.info("=" * 100)
        
        # Статистика по схемам
        all_schemas = set()
        user_schema_counts = {}
        
        for user_id, result in results.items():
            if "error" not in result:
                schemas = result.get("schemas_info", {})
                user_schema_counts[user_id] = len(schemas)
                all_schemas.update(schemas.keys())
            else:
                user_schema_counts[user_id] = 0
                logger.error(f"❌ Ошибка для пользователя {user_id}: {result['error']}")
        
        logger.info(f"📂 Всего уникальных схем в системе: {len(all_schemas)}")
        logger.info(f"📋 Схемы: {sorted(all_schemas)}")
        
        # Статистика доступа
        logger.info("👥 Доступ пользователей к схемам:")
        for user_id, schema_count in user_schema_counts.items():
            logger.info(f"   • {user_id}: {schema_count} схем")
        
        logger.info("=" * 100)
    
    def save_results_to_file(self, results: Dict[str, Any], filename: str = None):
        """Сохраняет результаты в JSON файл"""
        if filename is None:
            filename = f"schema_validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Результаты сохранены в файл: {filename}")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения результатов: {str(e)}")


async def main():
    """Основная функция для запуска проверки схем"""
    logger.info("🚀 Запуск проверки схем и доступных таблиц")
    
    validator = SchemaValidationLogger()
    
    # Пример использования - замените на реальные данные
    test_users = ["user1", "user2", "admin"]  # Замените на реальные ID пользователей
    database_name = "your_database"  # Замените на реальное имя базы данных
    
    try:
        # Проверяем одного пользователя
        logger.info("🔍 Проверка одного пользователя:")
        single_result = await validator.validate_schema_access("user1", database_name)
        
        # Проверяем нескольких пользователей
        logger.info("🔍 Проверка нескольких пользователей:")
        multiple_results = await validator.validate_multiple_users(test_users, database_name)
        
        # Сохраняем результаты
        validator.save_results_to_file(multiple_results)
        
        logger.info("✅ Проверка завершена успешно")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при выполнении проверки: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
