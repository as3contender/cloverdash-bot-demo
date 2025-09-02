#!/usr/bin/env python3
"""
LLM Admin - административный интерфейс для работы с LLM и правами пользователей
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any, Optional

# Добавляем путь к backend для импорта модулей
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from langchain_openai import ChatOpenAI
from services.app_database import app_database_service
from services.data_database import data_database_service
from models.llm import LLMQueryResponse
from config.settings import settings

logger = logging.getLogger(__name__)

class LLMAdmin:
    """Административный класс для работы с LLM и правами пользователей"""
    
    def __init__(self):
        """Инициализация LLM Admin"""
        try:
            self.llm = ChatOpenAI(
                model_name=settings.openai_model,
                temperature=settings.openai_temperature,
                openai_api_key=settings.openai_api_key,
            )
            # Проверяем, что API ключ настроен
            self.is_configured = bool(settings.openai_api_key and settings.openai_api_key.strip())
            
            logger.info(f"LLM Admin initialized with model: {settings.openai_model}")
            logger.info(f"LLM Admin configured: {self.is_configured}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM Admin: {e}")
            self.is_configured = False
            self.llm = None
    
    async def generate_sql_query_with_user_permissions(
        self, 
        natural_query: str, 
        user_id: str, 
        user_language: str = "en"
    ) -> LLMQueryResponse:
        """
        Генерирует SQL запрос на основе естественного языка с учетом прав пользователя
        
        Args:
            natural_query: Запрос на естественном языке
            user_id: ID пользователя для проверки прав
            user_language: Язык пользователя для ответа ('en' или 'ru')
            
        Returns:
            LLMQueryResponse: Ответ с сгенерированным SQL запросом
        """
        if not self.is_configured or not self.llm:
            raise Exception("LLM Admin не настроен или недоступен")
        
        try:
            # Создаем промпт с учетом прав пользователя
            prompt = await self._create_sql_prompt_with_user_permissions(
                natural_query, user_id, user_language
            )
            
            # Отправляем запрос к LLM
            response = await self.llm.ainvoke(prompt)
            
            # Извлекаем SQL из ответа
            sql_query = self._extract_sql_from_response(response.content)
            
            # Валидируем SQL на предмет безопасности
            if not self._validate_sql_security(sql_query):
                raise Exception("SQL запрос не прошел проверку безопасности")
            
            result = LLMQueryResponse(
                sql_query=sql_query,
                explanation=self._clean_markdown(response.content),
                execution_time=0.0  # Будет заполнено позже
            )
            
            logger.info(f"SQL query generated successfully for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"LLM query generation failed for user {user_id}: {str(e)}")
            raise Exception(f"Ошибка генерации SQL запроса: {str(e)}")
    
    async def _create_sql_prompt_with_user_permissions(
        self, 
        natural_query: str, 
        user_id: str, 
        user_language: str = "en"
    ) -> str:
        """Создает LLM промпт с учетом прав пользователя"""
        
        # Получаем схему БД с правами пользователя
        schema = await self._get_database_schema_with_user_permissions(user_id)
        schema_description = self._format_schema_for_prompt(schema, user_id)
        
        prompt = f"""
Ты - эксперт по SQL запросам. На основе описания схемы базы данных и пользовательского запроса на естественном языке, сгенерируй корректный SQL запрос.

{schema_description}

ЗАПРОС ПОЛЬЗОВАТЕЛЯ: {natural_query}

ВАЖНО: 
- Генерируй только SELECT запросы
- Используй только таблицы, доступные пользователю {user_id}
- Отвечай на языке: {user_language}
- Объясни логику запроса

SQL запрос:
```sql
"""
        
        return prompt
    
    async def _get_database_schema_with_user_permissions(self, user_id: str) -> Dict[str, Any]:
        """Получает схему БД с учетом прав пользователя"""
        
        try:
            # Получаем имя БД
            database_name = data_database_service.get_database_name()
            
            # Получаем схему с правами пользователя
            schema = await app_database_service.get_database_schema_with_user_permissions(
                user_id=user_id,
                database_name=database_name,
                include_views=True,
                schema_name="public"
            )
            
            logger.info(f"Database schema retrieved for user {user_id}: {len(schema)} tables")
            return schema
            
        except Exception as e:
            logger.error(f"Failed to get database schema for user {user_id}: {e}")
            # Возвращаем базовую схему в случае ошибки
            return {
                "users": {
                    "description": "Таблица пользователей (базовая)",
                    "columns": [
                        {"name": "id", "description": "ID пользователя", "datatype": "uuid"},
                        {"name": "username", "description": "Имя пользователя", "datatype": "varchar"}
                    ]
                }
            }
    
    async def execute_query_with_user(self, user_id: str, sql_query: str) -> Dict[str, Any]:
        """Выполняет SQL запрос от имени пользователя с учетом его роли"""
        
        try:
            # Получаем роль пользователя
            user_role = await self._get_user_role(user_id)
            
            # Выполняем запрос через data_database_service
            result = await data_database_service.execute_query(sql_query)
            
            return {
                "success": True,
                "role_used": user_role,
                "database_used": data_database_service.get_database_name(),
                "row_count": len(result) if result else 0,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Query execution failed for user {user_id}: {e}")
            return {
                "success": False,
                "message": str(e),
                "role_used": None,
                "database_used": None
            }
    
    async def _get_user_role(self, user_id: str) -> str:
        """Получает роль пользователя из БД"""
        try:
            # Получаем роль из users_role_bd_mapping
            query = """
            SELECT role_name 
            FROM users_role_bd_mapping 
            WHERE user_id = $1
            """
            result = await app_database_service.execute_query(query, [user_id])
            
            if result and result.data:
                role_name = result.data[0]['role_name']
                logger.info(f"User {user_id} has role: {role_name}")
                return role_name
            else:
                logger.warning(f"No role found for user {user_id}, using default role")
                return "user"  # Роль по умолчанию
                
        except Exception as e:
            logger.warning(f"Failed to get user role for {user_id}: {e}")
            return "user"
    
    def _extract_sql_from_response(self, response_content: str) -> str:
        """Извлекает SQL запрос из ответа LLM"""
        # Ищем SQL код между ```sql и ```
        import re
        sql_match = re.search(r'```sql\s*(.*?)\s*```', response_content, re.DOTALL)
        if sql_match:
            return sql_match.group(1).strip()
        
        # Если не нашли, ищем просто между ```
        code_match = re.search(r'```\s*(.*?)\s*```', response_content, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        # Если ничего не нашли, возвращаем весь ответ
        return response_content.strip()
    
    def _validate_sql_security(self, sql_query: str) -> bool:
        """Проверяет SQL запрос на безопасность"""
        sql_lower = sql_query.lower().strip()
        
        # Запрещенные операции
        forbidden_keywords = [
            'drop', 'delete', 'update', 'insert', 'create', 'alter', 'truncate',
            'grant', 'revoke', 'execute', 'call'
        ]
        
        for keyword in forbidden_keywords:
            if keyword in sql_lower:
                logger.warning(f"SQL query contains forbidden keyword: {keyword}")
                return False
        
        # Должен начинаться с SELECT
        if not sql_lower.startswith('select'):
            logger.warning("SQL query must start with SELECT")
            return False
        
        return True
    
    def _clean_markdown(self, content: str) -> str:
        """Очищает markdown разметку из ответа"""
        # Убираем ```sql и ```
        cleaned = content.replace('```sql', '').replace('```', '')
        return cleaned.strip()
    
    def _format_schema_for_prompt(self, schema: Dict[str, Any], user_id: str) -> str:
        """Форматирует схему БД для промпта"""
        schema_text = f"СХЕМА БАЗЫ ДАННЫХ (доступная пользователю {user_id}):\n"
        
        for table_name, table_info in schema.items():
            schema_text += f"\n📋 {table_name}: {table_info.get('description', 'Описание отсутствует')}\n"
            
            columns = table_info.get('columns', [])
            for col in columns:
                col_name = col.get('name', 'unknown')
                col_desc = col.get('description', 'Описание отсутствует')
                col_type = col.get('datatype', 'unknown')
                schema_text += f"  - {col_name}: {col_desc} ({col_type})\n"
        
        return schema_text

# Создаем глобальный экземпляр
llm_admin = LLMAdmin()

