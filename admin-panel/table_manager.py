import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import logging
from typing import Optional, Dict, Any, List
import sys
import os

# Добавляем путь к модулю app для импорта функций
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Импортируем функцию escape_json_for_postgres из app.py
try:
    from admin_panel.app import escape_json_for_postgres
except ImportError:
    # Fallback для случаев, когда импорт не работает
    def escape_json_for_postgres(json_str):
        return json_str

def get_sqlalchemy_engine():
    """Получить SQLAlchemy engine для подключения к базе данных"""
    try:
        from app.config.config import get_db_url
        return create_engine(get_db_url())
    except ImportError:
        # Fallback для случаев, когда импорт не работает
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        db_url = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/dbname')
        return create_engine(db_url)

def search_records(search_term: str, search_field: str = 'all') -> pd.DataFrame:
    """
    Поиск записей по различным полям
    
    Args:
        search_term: Термин для поиска
        search_field: Поле для поиска ('all', 'database_name', 'table_name', 'table_description', 'schema_name')
    
    Returns:
        DataFrame с результатами поиска
    """
    TABLE_NAME = 'public.database_despriptions_bacup'
    
    try:
        engine = get_sqlalchemy_engine()
        
        if search_field == 'all':
            query = f"""
                SELECT * FROM {TABLE_NAME} 
                WHERE database_name ILIKE :search_term 
                   OR table_name ILIKE :search_term 
                   OR table_description ILIKE :search_term 
                   OR schema_name ILIKE :search_term
                ORDER BY database_name, table_name
            """
        else:
            query = f"""
                SELECT * FROM {TABLE_NAME} 
                WHERE {search_field} ILIKE :search_term
                ORDER BY database_name, table_name
            """
        
        df = pd.read_sql(query, engine, params={'search_term': f'%{search_term}%'})
        
        # Очистить все строковые столбцы от невалидных байтов
        for col in df.select_dtypes(include=['object', 'string']).columns:
            df[col] = df[col].apply(clean_text)
        
        logging.info(f'Найдено {len(df)} записей по поиску "{search_term}" в поле "{search_field}"')
        return df
        
    except Exception as e:
        logging.error(f'Ошибка при поиске записей: {e}', exc_info=True)
        return pd.DataFrame()

def filter_records(filters: Dict[str, Any]) -> pd.DataFrame:
    """
    Фильтрация записей по различным критериям
    
    Args:
        filters: Словарь с фильтрами {field: value}
    
    Returns:
        DataFrame с отфильтрованными результатами
    """
    TABLE_NAME = 'public.database_despriptions_bacup'
    
    try:
        engine = get_sqlalchemy_engine()
        
        # Строим WHERE условия
        where_conditions = []
        params = {}
        
        for field, value in filters.items():
            if value and str(value).strip():
                where_conditions.append(f"{field} = :{field}")
                params[field] = value
        
        if where_conditions:
            query = f"""
                SELECT * FROM {TABLE_NAME} 
                WHERE {' AND '.join(where_conditions)}
                ORDER BY database_name, table_name
            """
        else:
            query = f"SELECT * FROM {TABLE_NAME} ORDER BY database_name, table_name"
        
        df = pd.read_sql(query, engine, params=params)
        
        # Очистить все строковые столбцы от невалидных байтов
        for col in df.select_dtypes(include=['object', 'string']).columns:
            df[col] = df[col].apply(clean_text)
        
        logging.info(f'Отфильтровано {len(df)} записей по критериям: {filters}')
        return df
        
    except Exception as e:
        logging.error(f'Ошибка при фильтрации записей: {e}', exc_info=True)
        return pd.DataFrame()

def get_statistics() -> Dict[str, Any]:
    """
    Получить статистику по таблице
    
    Returns:
        Словарь со статистикой
    """
    TABLE_NAME = 'public.database_despriptions_bacup'
    
    try:
        engine = get_sqlalchemy_engine()
        
        # Общее количество записей
        total_count = pd.read_sql(f"SELECT COUNT(*) as count FROM {TABLE_NAME}", engine).iloc[0]['count']
        
        # Количество по типам объектов
        object_types = pd.read_sql(f"""
            SELECT object_type, COUNT(*) as count 
            FROM {TABLE_NAME} 
            GROUP BY object_type 
            ORDER BY count DESC
        """, engine)
        
        # Количество по схемам
        schemas = pd.read_sql(f"""
            SELECT schema_name, COUNT(*) as count 
            FROM {TABLE_NAME} 
            GROUP BY schema_name 
            ORDER BY count DESC
        """, engine)
        
        # Количество по базам данных
        databases = pd.read_sql(f"""
            SELECT database_name, COUNT(*) as count 
            FROM {TABLE_NAME} 
            GROUP BY database_name 
            ORDER BY count DESC
        """, engine)
        
        # Записи с пустыми описаниями
        empty_descriptions = pd.read_sql(f"""
            SELECT COUNT(*) as count 
            FROM {TABLE_NAME} 
            WHERE table_description IS NULL OR table_description = ''
        """, engine).iloc[0]['count']
        
        return {
            'total_records': total_count,
            'object_types': object_types.to_dict('records'),
            'schemas': schemas.to_dict('records'),
            'databases': databases.to_dict('records'),
            'empty_descriptions': empty_descriptions
        }
        
    except Exception as e:
        logging.error(f'Ошибка при получении статистики: {e}', exc_info=True)
        return {}

def bulk_update_descriptions(updates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Массовое обновление описаний
    
    Args:
        updates: Список словарей с обновлениями [{'id': 1, 'table_description': 'new desc'}, ...]
    
    Returns:
        Словарь с результатами операции
    """
    TABLE_NAME = 'public.database_despriptions_bacup'
    
    try:
        engine = get_sqlalchemy_engine()
        success_count = 0
        error_count = 0
        errors = []
        
        with engine.connect() as conn:
            for update in updates:
                try:
                    conn.execute(
                        text(f"""
                            UPDATE {TABLE_NAME}
                            SET table_description = :table_description, 
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = :id
                        """),
                        {
                            "table_description": escape_json_for_postgres(update['table_description']),
                            "id": update['id']
                        }
                    )
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    errors.append(f"ID {update['id']}: {str(e)}")
            
            conn.commit()
        
        logging.info(f'Массовое обновление завершено. Успешно: {success_count}, Ошибок: {error_count}')
        
        return {
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors
        }
        
    except Exception as e:
        logging.error(f'Ошибка при массовом обновлении: {e}', exc_info=True)
        return {'success_count': 0, 'error_count': len(updates), 'errors': [str(e)]}

def export_data(format_type: str = 'csv') -> bytes:
    """
    Экспорт данных в различных форматах
    
    Args:
        format_type: Тип формата ('csv', 'excel', 'json')
    
    Returns:
        Байты с данными
    """
    TABLE_NAME = 'public.database_despriptions_bacup'
    
    try:
        engine = get_sqlalchemy_engine()
        df = pd.read_sql(f'SELECT * FROM {TABLE_NAME}', engine)
        
        # Очистить все строковые столбцы от невалидных байтов
        for col in df.select_dtypes(include=['object', 'string']).columns:
            df[col] = df[col].apply(clean_text)
        
        if format_type == 'csv':
            return df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        elif format_type == 'excel':
            from io import BytesIO
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Database Descriptions')
            return output.getvalue()
        elif format_type == 'json':
            return df.to_json(orient='records', force_ascii=False, indent=2).encode('utf-8')
        else:
            raise ValueError(f'Неподдерживаемый формат: {format_type}')
            
    except Exception as e:
        logging.error(f'Ошибка при экспорте данных: {e}', exc_info=True)
        raise

def clean_text(text):
    """Очищает текст, заменяя невалидные байты на символ замены."""
    if text is None:
        return ''
    if isinstance(text, bytes):
        return text.decode('utf-8', errors='replace')
    return str(text).encode('utf-8', errors='replace').decode('utf-8')

def validate_record_data(data: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Валидация данных записи
    
    Args:
        data: Словарь с данными записи
    
    Returns:
        Словарь с ошибками валидации
    """
    errors = []
    
    # Проверка обязательных полей
    if not data.get('database_name', '').strip():
        errors.append('Database Name обязателен')
    
    if not data.get('table_name', '').strip():
        errors.append('Table Name обязателен')
    
    # Проверка длины полей
    if len(data.get('database_name', '')) > 255:
        errors.append('Database Name слишком длинный (максимум 255 символов)')
    
    if len(data.get('table_name', '')) > 255:
        errors.append('Table Name слишком длинный (максимум 255 символов)')
    
    if len(data.get('schema_name', '')) > 255:
        errors.append('Schema Name слишком длинный (максимум 255 символов)')
    
    # Проверка допустимых значений
    valid_object_types = ['table', 'view', 'function', 'procedure']
    if data.get('object_type') and data['object_type'] not in valid_object_types:
        errors.append(f'Object Type должен быть одним из: {", ".join(valid_object_types)}')
    
    return {'errors': errors}

def validate_user_table_access(data: Dict[str, Any], username: str = None) -> Dict[str, List[str]]:
    """
    Валидация доступа пользователя к таблице
    
    Args:
        data: Словарь с данными записи (database_name, schema_name, table_name)
        username: имя пользователя для проверки доступа
    
    Returns:
        Словарь с ошибками валидации доступа
    """
    errors = []
    
    if not username:
        return {'errors': errors}
    
    try:
        # Импортируем функции из app.py
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from app import validate_user_table_access as check_access
        
        database_name = data.get('database_name', '').strip()
        schema_name = data.get('schema_name', '').strip()
        table_name = data.get('table_name', '').strip()
        
        if database_name and schema_name and table_name:
            if not check_access(username, database_name, schema_name, table_name):
                errors.append(f'У пользователя {username} нет доступа к таблице {database_name}.{schema_name}.{table_name}')
        
    except Exception as e:
        errors.append(f'Ошибка при проверке доступа: {str(e)}')
    
    return {'errors': errors}

def validate_user_schema_access(schema_name: str, username: str = None) -> Dict[str, List[str]]:
    """
    Валидация доступа пользователя к схеме
    
    Args:
        schema_name: название схемы
        username: имя пользователя для проверки доступа
    
    Returns:
        Словарь с ошибками валидации доступа
    """
    errors = []
    
    if not username or not schema_name:
        return {'errors': errors}
    
    try:
        # Импортируем функции из app.py
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from app import get_user_accessible_schemas
        
        accessible_schemas = get_user_accessible_schemas(username)
        
        if schema_name not in accessible_schemas:
            errors.append(f'У пользователя {username} нет доступа к схеме {schema_name}. Доступные схемы: {", ".join(accessible_schemas) if accessible_schemas else "нет"}')
        
    except Exception as e:
        errors.append(f'Ошибка при проверке доступа к схеме: {str(e)}')
    
    return {'errors': errors}

def get_table_structure() -> List[Dict[str, Any]]:
    """
    Получить структуру таблицы
    
    Returns:
        Список словарей с информацией о колонках
    """
    TABLE_NAME = 'public.database_despriptions_bacup'
    
    try:
        engine = get_sqlalchemy_engine()
        
        # Получаем информацию о колонках
        query = f"""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length
            FROM information_schema.columns 
            WHERE table_name = 'database_despriptions_bacup' 
              AND table_schema = 'public'
            ORDER BY ordinal_position
        """
        
        df = pd.read_sql(query, engine)
        
        columns_info = []
        for _, row in df.iterrows():
            columns_info.append({
                'name': row['column_name'],
                'type': row['data_type'],
                'nullable': row['is_nullable'] == 'YES',
                'default': row['column_default'],
                'max_length': row['character_maximum_length']
            })
        
        return columns_info
        
    except Exception as e:
        logging.error(f'Ошибка при получении структуры таблицы: {e}', exc_info=True)
        return [] 