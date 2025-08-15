#!/usr/bin/env python3
"""
CRUD операции для словарей колонок базы данных
Согласно описанию.cd
"""

import json
import logging
from typing import Dict, Any, Optional
from sqlalchemy import create_engine, text
from psycopg2.extras import Json

class DictCRUD:
    """Класс для CRUD операций со словарями колонок"""
    
    def __init__(self, engine):
        self.engine = engine
        self.table_name = 'database_descriptions_backup'
    
    def _get_current_table_desc(self, id: int) -> Dict[str, Any]:
        """Получает текущий table_description из БД"""
        try:
            with self.engine.connect() as conn:
                select_query = f"""
                    SELECT table_description FROM {self.table_name}
                    WHERE id = :id
                """
                result = conn.execute(text(select_query), {
                    'id': id
                })
                row = result.fetchone()
                
                if row:
                    current_table_desc = row[0]
                    
                    # Парсим JSON если нужно
                    if isinstance(current_table_desc, str):
                        try:
                            current_table_desc = json.loads(current_table_desc)
                        except json.JSONDecodeError:
                            current_table_desc = {}
                    elif current_table_desc is None:
                        current_table_desc = {}
                    
                    return current_table_desc
                else:
                    return {}
                    
        except Exception as e:
            logging.error(f'Ошибка получения данных из БД: {e}')
            return {}
    
    def _update_table_description(self, id: int, table_desc: Dict[str, Any]) -> bool:
        """Обновляет table_description в БД"""
        try:
            with self.engine.connect() as conn:
                update_query = f"""
                    UPDATE {self.table_name}
                    SET table_description = :table_desc, updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                """
                
                conn.execute(text(update_query), {
                    'table_desc': Json(table_desc),
                    'id': id
                })
                
                conn.commit()
                return True
                
        except Exception as e:
            logging.error(f'Ошибка обновления в БД: {e}')
            return False
    
    def save_column_description(self, id: int, 
                              column_name: str, column_data: Dict[str, Any], is_new_column: bool = False) -> bool:
        """
        Сохранение описания колонки в БД согласно логике из описания.cd
        
        Args:
            database_name: название базы данных
            schema_name: название схемы
            table_name: название таблицы
            column_name: название колонки (ключ в словаре)
            column_data: данные колонки {datatype, placeholder, теги, описание}
            is_new_column: флаг новой колонки (true - добавление, false - редактирование)
        """
        # Проверяем, не пытается ли пользователь изменить системное поле id или ключ key
        if column_name == 'id':
            logging.warning(f'Попытка изменить системное поле id в записи {id}')
            return False
        
        if column_name == 'key' and not is_new_column:
            logging.warning(f'Попытка изменить ключ key в записи {id}')
            return False
        
        try:
            # Получаем текущие данные из БД
            current_table_desc = self._get_current_table_desc(id)
            
            # Согласно логике из описания.cd
            if is_new_column:
                # Добавление новой колонки
                _dict_key = column_name  # "key" если new_column = true
            else:
                # Редактирование существующей колонки
                _dict_key = column_name  # "_current_column" если new_column = false
            
            # Собираем объект для записи в словарь
            _new_object = {
                'datatype': column_data.get('datatype', ''),
                'placeholder': column_data.get('placeholder', ''),
                'теги': column_data.get('теги', []),
                'описание': column_data.get('описание', '')
            }
            
            # Проверяем, есть ли секция columns в структуре
            if 'columns' in current_table_desc:
                # Обновляем в секции columns
                current_table_desc['columns'][_dict_key] = _new_object
                logging.info(f'Обновляем в секции columns: {_dict_key} = {_new_object}')
            else:
                # Если секции columns нет, создаем её
                if 'columns' not in current_table_desc:
                    current_table_desc['columns'] = {}
                current_table_desc['columns'][_dict_key] = _new_object
                logging.info(f'Создаем секцию columns и обновляем: {_dict_key} = {_new_object}')
            
            # Делаем Update в БД
            if self._update_table_description(id, current_table_desc):
                logging.info(f'Колонка {column_name} успешно {"добавлена" if is_new_column else "обновлена"}')
                return True
            else:
                return False
                
        except Exception as e:
            logging.error(f'Ошибка сохранения колонки {column_name}: {e}')
            return False
    
    def delete_column_description(self, id: int, column_name: str) -> bool:
        """
        Удаление описания колонки из БД
        
        Args:
            id: ID записи в БД
            column_name: название колонки для удаления
        """
        # Специальная обработка для колонки 'key'
        if column_name == 'key':
            logging.warning(f'Попытка удалить системную колонку key в записи {id}')
            return False
        
        try:
            # Получаем текущие данные из БД
            current_table_desc = self._get_current_table_desc(id)
            
            # Удаляем колонку из секции columns
            if 'columns' in current_table_desc and column_name in current_table_desc['columns']:
                del current_table_desc['columns'][column_name]
                logging.info(f'Колонка {column_name} удалена из секции columns')
                
                # Обновляем в БД
                if self._update_table_description(id, current_table_desc):
                    logging.info(f'Колонка {column_name} успешно удалена')
                    return True
                else:
                    return False
            else:
                logging.warning(f'Колонка {column_name} не найдена в записи {id}')
                return False
                
        except Exception as e:
            logging.error(f'Ошибка удаления колонки {column_name}: {e}')
            return False
    
    def get_column_description(self, id: int, column_name: str) -> Optional[Dict[str, Any]]:
        """
        Получение описания колонки из БД
        
        Args:
            database_name: название базы данных
            schema_name: название схемы
            table_name: название таблицы
            column_name: название колонки
            
        Returns:
            Словарь с описанием колонки или None если не найдено
        """
        try:
            current_table_desc = self._get_current_table_desc(id)
            
            if 'columns' in current_table_desc and column_name in current_table_desc['columns']:
                return current_table_desc['columns'][column_name]
            else:
                return None
                
        except Exception as e:
            logging.error(f'Ошибка получения описания колонки {column_name}: {e}')
            return None
    
    def list_all_columns(self, id: int) -> Dict[str, Any]:
        """
        Получение списка всех колонок для таблицы
        
        Args:
            database_name: название базы данных
            schema_name: название схемы
            table_name: название таблицы
            
        Returns:
            Словарь всех колонок или пустой словарь
        """
        try:
            current_table_desc = self._get_current_table_desc(id)
            
            if 'columns' in current_table_desc:
                return current_table_desc['columns']
            else:
                return {}
                
        except Exception as e:
            logging.error(f'Ошибка получения списка колонок: {e}')
            return {}
