from dotenv import load_dotenv
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from config import DB_CONFIG, get_db_url
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import json
import logging
from psycopg2.extras import Json

# Импортируем новый класс DictCRUD
from dict_crud import DictCRUD

# Загружаем .env файл из корня проекта
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)

TABLE_NAME = 'public.database_descriptions_backup'
sqlalchemy_engine = None

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('admin_panel.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def get_dynamic_db_config():
    """
    Получить параметры подключения к БД из session_state или из переменных окружения.
    """
    config = {}
    config['host'] = st.session_state.get('db_host') or os.getenv('APP_DATABASE_HOST')
    config['port'] = int(st.session_state.get('db_port') or os.getenv('APP_DATABASE_PORT', '5432'))
    config['user'] = st.session_state.get('db_user') or os.getenv('APP_DATABASE_USER')
    config['password'] = st.session_state.get('db_password') or os.getenv('APP_DATABASE_PASSWORD')
    config['database'] = st.session_state.get('db_name') or os.getenv('APP_DATABASE_NAME')
    return config

def get_sqlalchemy_engine():
    global sqlalchemy_engine
    if sqlalchemy_engine:
        return sqlalchemy_engine
    logging.info('Создание SQLAlchemy engine для подключения к базе данных.')
    config = get_dynamic_db_config()
    url = (
        f"postgresql+psycopg2://{config['user']}:{config['password']}@"
        f"{config['host']}:{config['port']}/{config['database']}?sslmode=require"
    )
    sqlalchemy_engine = create_engine(url)
    return sqlalchemy_engine

def load_data():
    try:
        logging.info('Загрузка данных из таблицы %s', TABLE_NAME)
        engine = get_sqlalchemy_engine()
        df = pd.read_sql(f'SELECT * FROM {TABLE_NAME}', engine)
        
        # Очистить все строковые столбцы от невалидных байтов
        for col in df.select_dtypes(include=['object', 'string']).columns:
            df[col] = df[col].apply(clean_text)
        
        # Обрабатываем JSON поля - нормализуем типы данных для совместимости с Arrow
        if 'table_description' in df.columns:
            df['table_description'] = df['table_description'].apply(normalize_table_description)
        
        # Дополнительная проверка на совместимость с Arrow
        try:
            # Пытаемся преобразовать DataFrame в Arrow формат для проверки
            import pyarrow as pa
            pa.Table.from_pandas(df)
            logging.info('DataFrame успешно протестирован на совместимость с Arrow')
        except Exception as arrow_error:
            logging.warning(f'Проблема совместимости с Arrow: {arrow_error}')
            # Принудительно конвертируем проблемные колонки в строки
            for col in df.select_dtypes(include=['object']).columns:
                df[col] = df[col].astype(str)
            logging.info('Проблемные колонки конвертированы в строки для совместимости с Arrow')
        
        logging.info('Данные успешно загружены. Количество строк: %d', len(df))
        return df
    except Exception as e:
        logging.error('Ошибка подключения к базе данных: %s', e, exc_info=True)
        st.error(f'Ошибка подключения к базе данных: {e}')
        return pd.DataFrame()

def clean_text(text):
    """Очищает текст, заменяя невалидные байты на символ замены."""
    if text is None:
        return ''
    if isinstance(text, bytes):
        return text.decode('utf-8', errors='replace')
    return str(text).encode('utf-8', errors='replace').decode('utf-8')

def normalize_table_description(value):
    """
    Нормализует значения в колонке table_description для совместимости с Arrow.
    Преобразует все значения в строки JSON для избежания ошибок сериализации.
    """
    if value is None:
        return None
    
    try:
        # Если это уже словарь, преобразуем в JSON строку
        if isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False)
        
        # Если это строка, проверяем, является ли она валидным JSON
        if isinstance(value, str):
            # Пытаемся распарсить и переформатировать для единообразия
            try:
                parsed = json.loads(value)
                return json.dumps(parsed, ensure_ascii=False)
            except json.JSONDecodeError:
                # Если это не JSON, возвращаем как есть
                return value
        
        # Если это объект Json из psycopg2, преобразуем в строку
        if hasattr(value, '__str__'):
            try:
                parsed = json.loads(str(value))
                return json.dumps(parsed, ensure_ascii=False)
            except json.JSONDecodeError:
                return str(value)
        
        # Для всех остальных типов возвращаем строковое представление
        return str(value)
        
    except Exception as e:
        logging.warning(f"Ошибка при нормализации table_description: {e}")
        return str(value) if value is not None else None

def save_column_description(database_name, schema_name, table_name, column_name, column_data, is_new_column=False):
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
    try:
        engine = get_sqlalchemy_engine()
        
        # Получаем ID записи по database_name, schema_name, table_name
        query = """
            SELECT id FROM database_descriptions_backup 
            WHERE database_name = :db_name AND schema_name = :schema_name AND table_name = :table_name
        """
        with engine.connect() as conn:
            result = conn.execute(text(query), {
                'db_name': database_name,
                'schema_name': schema_name,
                'table_name': table_name
            })
            row = result.fetchone()
            if not row:
                logging.error(f'Запись не найдена: {database_name}.{schema_name}.{table_name}')
                return False
            
            record_id = row[0]
        
        dict_crud = DictCRUD(engine)
        return dict_crud.save_column_description(record_id, column_name, column_data, is_new_column)
    except Exception as e:
        logging.error(f'Ошибка сохранения колонки {column_name}: {e}')
        return False

def delete_column_description(database_name, schema_name, table_name, column_name):
    """
    Удаление описания колонки из БД
    
    Args:
        database_name: название базы данных
        schema_name: название схемы
        table_name: название таблицы
        column_name: название колонки для удаления
    """
    try:
        engine = get_sqlalchemy_engine()
        
        # Получаем ID записи по database_name, schema_name, table_name
        query = """
            SELECT id FROM database_descriptions_backup 
            WHERE database_name = :db_name AND schema_name = :schema_name AND table_name = :table_name
        """
        with engine.connect() as conn:
            result = conn.execute(text(query), {
                'db_name': database_name,
                'schema_name': schema_name,
                'table_name': table_name
            })
            row = result.fetchone()
            if not row:
                logging.error(f'Запись не найдена: {database_name}.{schema_name}.{table_name}')
                return False
            
            record_id = row[0]
        
        dict_crud = DictCRUD(engine)
        return dict_crud.delete_column_description(record_id, column_name)
    except Exception as e:
        logging.error(f'Ошибка удаления колонки {column_name}: {e}')
        return False

def delete_record(database_name, schema_name, table_name):
    """
    Удаление записи из БД
    """
    try:
        # Логируем действие пользователя
        current_user = st.session_state.get('username', 'Неизвестно')
        logging.info(f'Пользователь {current_user} пытается удалить запись {database_name}.{schema_name}.{table_name}')
        
        engine = get_sqlalchemy_engine()
        
        with engine.connect() as conn:
            # Удаляем запись из БД
            delete_query = """
                DELETE FROM database_descriptions_backup 
                WHERE database_name = :db_name AND schema_name = :schema_name AND table_name = :table_name
            """
            
            result = conn.execute(text(delete_query), {
                'db_name': database_name,
                'schema_name': schema_name,
                'table_name': table_name
            })
            
            conn.commit()
            
            if result.rowcount > 0:
                logging.info(f'Пользователь {current_user} успешно удалил запись {database_name}.{schema_name}.{table_name}')
                return True
            else:
                logging.warning(f'Пользователь {current_user}: запись {database_name}.{schema_name}.{table_name} не найдена')
                return False
                
    except Exception as e:
        current_user = st.session_state.get('username', 'Неизвестно')
        logging.error(f'Пользователь {current_user}: ошибка при удалении записи {database_name}.{schema_name}.{table_name}: {e}', exc_info=True)
        return False

def get_database_descriptions():
    """Получение всех записей из таблицы database_descriptions_backup"""
    try:
        engine = get_sqlalchemy_engine()
        query = "SELECT * FROM database_descriptions_backup ORDER BY database_name, schema_name, table_name"
        df = pd.read_sql_query(query, engine)
        return df
    except Exception as e:
        logging.error(f"Ошибка получения данных из БД: {e}")
        return pd.DataFrame()

def get_record_by_id(record_id):
    """Получить запись по ID"""
    try:
        engine = get_sqlalchemy_engine()
        query = "SELECT * FROM database_descriptions_backup WHERE id = :record_id"
        with engine.connect() as conn:
            result = conn.execute(text(query), {"record_id": record_id})
            row = result.fetchone()
            if row:
                columns = result.keys()
                return dict(zip(columns, row))
        return None
    except Exception as e:
        logging.error(f"Ошибка при поиске записи: {e}")
        return None

def get_available_ids():
    """Получить список доступных ID записей"""
    try:
        engine = get_sqlalchemy_engine()
        query = 'SELECT id, database_name, schema_name, table_name FROM database_descriptions_backup ORDER BY id'
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        logging.error('Ошибка при получении списка ID: %s', e, exc_info=True)
        return pd.DataFrame()

def parse_table_description(table_description):
    """
    Парсит описание таблицы из JSONB поля
    """
    if not table_description:
        return {}
    
    try:
        # Если это уже словарь, возвращаем как есть
        if isinstance(table_description, dict):
            return table_description
        
        # Если это строка, пытаемся распарсить JSON
        if isinstance(table_description, str):
            # Убираем лишние пробелы и проверяем на пустую строку
            if table_description.strip() == '':
                return {}
            return json.loads(table_description)
        
        # Если это объект Json из psycopg2, преобразуем в строку и парсим
        if hasattr(table_description, '__str__'):
            str_value = str(table_description)
            if str_value.strip() == '':
                return {}
            return json.loads(str_value)
        
        # Если ничего не подходит, возвращаем пустой словарь
        return {}
        
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        logging.warning(f"Ошибка при парсинге table_description: {e}")
        return {}

def add_new_record(database_name, schema_name, table_name, object_type, description, table_description):
    """
    Добавление новой записи в БД
    
    Args:
        database_name: название базы данных
        schema_name: название схемы
        table_name: название таблицы
        object_type: тип объекта
        description: общее описание (не используется, так как поля нет в таблице)
        table_description: JSON описание колонок
    """
    try:
        # Логируем действие пользователя
        current_user = st.session_state.get('username', 'Неизвестно')
        logging.info(f'Пользователь {current_user} пытается добавить запись: {database_name}.{schema_name}.{table_name}')
        logging.info(f'Параметры: object_type={object_type}, description={description}, table_description={table_description}')
        
        engine = get_sqlalchemy_engine()
        logging.info('SQLAlchemy engine создан успешно')
        
        with engine.connect() as conn:
            logging.info('Соединение с БД установлено')
            
            # Проверяем, не существует ли уже такая запись
            check_query = """
                SELECT COUNT(*) FROM database_descriptions_backup 
                WHERE database_name = :db_name AND schema_name = :schema_name AND table_name = :table_name
            """
            logging.info(f'Выполняем проверку существования записи: {check_query}')
            
            result = conn.execute(text(check_query), {
                'db_name': database_name,
                'schema_name': schema_name,
                'table_name': table_name
            })
            count = result.scalar()
            logging.info(f'Количество существующих записей: {count}')
            
            if count > 0:
                logging.warning(f'Запись уже существует: {database_name}.{schema_name}.{table_name}')
                return False
            
            # Добавляем новую запись (без поля description)
            insert_query = """
                INSERT INTO database_descriptions_backup 
                (database_name, schema_name, table_name, object_type, table_description, created_at, updated_at)
                VALUES (:db_name, :schema_name, :table_name, :obj_type, :table_desc, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
            logging.info(f'Выполняем INSERT запрос: {insert_query}')
            
            # Подготавливаем параметры для вставки (без description)
            insert_params = {
                'db_name': database_name,
                'schema_name': schema_name,
                'table_name': table_name,
                'obj_type': object_type,
                'table_desc': Json(table_description) if table_description else None
            }
            logging.info(f'Параметры для вставки: {insert_params}')
            
            conn.execute(text(insert_query), insert_params)
            logging.info('INSERT запрос выполнен успешно')
            
            conn.commit()
            logging.info('Транзакция зафиксирована')
            
            logging.info(f'Пользователь {current_user} успешно добавил запись: {database_name}.{schema_name}.{table_name}')
            return True
                
    except Exception as e:
        current_user = st.session_state.get('username', 'Неизвестно')
        logging.error(f'Пользователь {current_user}: ошибка при добавлении записи {database_name}.{schema_name}.{table_name}: {e}', exc_info=True)
        logging.error(f'Тип ошибки: {type(e).__name__}')
        logging.error(f'Детали ошибки: {str(e)}')
        return False

# =============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =============================================================================

def format_tags_for_display(tags_value):
    """Форматирует теги для отображения в DataFrame"""
    if isinstance(tags_value, list):
        return ', '.join(tags_value)
    else:
        return str(tags_value) if tags_value else ''

def create_column_dataframe(table_desc):
    """Создает DataFrame для отображения колонок"""
    columns_data = []
    for col_name, col_info in table_desc.items():
        if isinstance(col_info, dict):
            # Проверяем, является ли это системным полем или ключом
            is_system_field = col_name == 'id'
            is_key_field = col_name == 'key'
            if is_system_field:
                status = "🔒 Системное поле"
            elif is_key_field:
                status = "🔑 Ключ (недоступно для редактирования)"
            else:
                status = "✏️ Доступно для редактирования"
            
            # Приводим теги к строке для избежания конфликта типов в DataFrame
            tags_display = format_tags_for_display(col_info.get('теги', ''))
            
            columns_data.append({
                'Колонка': col_name, 
                'Datatype': str(col_info.get('datatype', '')),
                'Tags': tags_display,
                'Placeholder': str(col_info.get('placeholder', '')),
                'Description': str(col_info.get('описание', '')),
                'Статус': status
            })
        else:
            # Если col_info не словарь, показываем как есть
            is_system_field = col_name == 'id'
            is_key_field = col_name == 'key'
            if is_system_field:
                status = "🔒 Системное поле"
            elif is_key_field:
                status = "🔑 Ключ (недоступно для редактирования)"
            else:
                status = "❓ Неизвестный тип"
            
            columns_data.append({
                'Колонка': col_name,
                'Datatype': str(col_info),
                'Tags': '',
                'Placeholder': '',
                'Description': '',
                'Статус': status
            })
    
    # Сортируем колонки: сначала 'key', затем остальные
    if columns_data:
        # Разделяем на ключевые и обычные колонки
        key_columns = [col for col in columns_data if col['Колонка'] == 'key']
        other_columns = [col for col in columns_data if col['Колонка'] != 'key']
        
        # Сортируем обычные колонки по алфавиту
        other_columns.sort(key=lambda x: x['Колонка'])
        
        # Объединяем: сначала ключевые, затем остальные
        sorted_columns_data = key_columns + other_columns
        
        return pd.DataFrame(sorted_columns_data)
    
    return pd.DataFrame(columns_data) if columns_data else None

def display_record_info(selected_data):
    """Отображает информацию о записи в стиле _format_schema_for_prompt"""
    st.subheader("📋 Информация о записи")
    
    # Определяем тип объекта
    object_type = selected_data.get('object_type', 'table')
    schema_name = selected_data.get('schema_name', 'public')
    table_name = selected_data.get('table_name', '')
    
    # Показываем тип объекта (таблица или представление)
    object_label = "ПРЕДСТАВЛЕНИЕ" if object_type == "view" else "ТАБЛИЦА"
    full_name = f"{schema_name}.{table_name}" if schema_name != "public" else table_name
    
    st.info(f"**{object_label}:** {full_name}")
    
    # Показываем описание, если есть
    if selected_data.get('description'):
        st.info(f"**ОПИСАНИЕ:** {selected_data['description']}")

def display_detailed_columns(table_desc):
    """Отображает детальное описание колонок в стиле _format_schema_for_prompt"""
    st.subheader("📝 Детальное описание колонок:")
    for col_name, col_info in table_desc.items():
        if isinstance(col_info, dict):
            col_type = col_info.get('datatype', '')
            col_desc = col_info.get('описание', '')
            col_tags = col_info.get('теги', '')
            
            # Форматируем теги
            if isinstance(col_tags, list):
                tags_display = ', '.join(col_tags)
            else:
                tags_display = str(col_tags) if col_tags else ''
            
            # Показываем колонку в стиле _format_schema_for_prompt
            if col_name == 'key':
                col_text = f"  - {col_name} ({col_type}) [🔑 КЛЮЧ]"
            elif col_name == 'id':
                col_text = f"  - {col_name} ({col_type}) [🔒 СИСТЕМНОЕ ПОЛЕ]"
            else:
                col_text = f"  - {col_name} ({col_type})"
            
            if col_desc:
                col_text += f" - {col_desc}"
            if tags_display:
                col_text += f" [теги: {tags_display}]"
            
            st.text(col_text)
        else:
            if col_name == 'key':
                st.text(f"  - {col_name} ({str(col_info)}) [🔑 КЛЮЧ]")
            elif col_name == 'id':
                st.text(f"  - {col_name} ({str(col_info)}) [🔒 СИСТЕМНОЕ ПОЛЕ]")
            else:
                st.text(f"  - {col_name} ({str(col_info)})")

def create_edit_form(selected_column, current_col_info, selected_data):
    """Создает форму редактирования колонки"""
    with st.form(f"edit_column_{selected_column}"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_datatype = st.text_input(
                "Datatype",
                value=current_col_info.get('datatype', ''),
                help="Тип данных колонки",
                key=f"edit_datatype_{selected_column}"
            )
            
            new_placeholder = st.text_input(
                "Placeholder",
                value=current_col_info.get('placeholder', ''),
                help="Пример значения",
                key=f"edit_placeholder_{selected_column}"
            )
        
        with col2:
            # Корректно обрабатываем теги для отображения в форме
            current_tags = current_col_info.get('теги', [])
            if isinstance(current_tags, list):
                tags_display = ', '.join(current_tags)
            else:
                tags_display = str(current_tags) if current_tags else ''
            
            new_tags = st.text_input(
                "Теги (через запятую)",
                value=tags_display,
                help="Теги через запятую",
                key=f"edit_tags_{selected_column}"
            )
            
            new_description = st.text_area(
                "Описание",
                value=current_col_info.get('описание', ''),
                help="Описание колонки",
                key=f"edit_description_{selected_column}"
            )
        
        # Переключатель для режима добавления/редактирования
        is_new_column = st.checkbox(
            "Добавить новую колонку (new_column = true)",
            value=False,
            help="Если включено - добавляется новая колонка, если выключено - редактируется существующая",
            key=f"edit_new_column_{selected_column}"
        )
        
        # Создаем объект для отображения в информационных блоках
        preview_object = {
            'datatype': new_datatype,
            'placeholder': new_placeholder,
            'теги': [tag.strip() for tag in new_tags.split(',') if tag.strip()] if new_tags else [],
            'описание': new_description
        }
        
        # Кнопки действий
        col1, col2, col3 = st.columns(3)
        
        with col1:
            save_clicked = st.form_submit_button("💾 Save")
        
        with col2:
            delete_clicked = st.form_submit_button("🗑️ Удалить поле")
        
        with col3:
            refresh_clicked = st.form_submit_button("🔄 Обновить")
        
        # Проверяем ограничения для колонки 'key' ПОСЛЕ создания кнопок
        if selected_column == 'key' and not is_new_column:
            st.warning("⚠️ Колонка 'key' недоступна для редактирования!")
            st.info("🔑 Для изменения колонки 'key' включите галочку 'Добавить новую колонку'")
            
            # Показываем текущие данные колонки key только для чтения
            st.subheader("📋 Текущие данные колонки 'key':")
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Datatype", value=current_col_info.get('datatype', ''), disabled=True)
                st.text_input("Placeholder", value=current_col_info.get('placeholder', ''), disabled=True)
            with col2:
                tags_display = ', '.join(current_col_info.get('теги', [])) if isinstance(current_col_info.get('теги', []), list) else str(current_col_info.get('теги', ''))
                st.text_input("Теги", value=tags_display, disabled=True)
                st.text_area("Описание", value=current_col_info.get('описание', ''), disabled=True)
            
            st.info("💡 Включите галочку выше для создания новой колонки 'key'")
            # НЕ возвращаем None здесь, чтобы кнопки остались активными
        else:
            # Обработка действий только если колонка доступна для редактирования
            if save_clicked:
                return handle_save_column(selected_column, preview_object, is_new_column, selected_data)
            elif delete_clicked:
                return handle_delete_column(selected_column, selected_data)
            elif refresh_clicked:
                st.rerun()
        
        return None
        


def handle_save_column(selected_column, preview_object, is_new_column, selected_data):
    """Обрабатывает сохранение колонки"""
    # Собираем объект для записи согласно описание.cd
    _new_object = {
        'datatype': preview_object['datatype'],
        'placeholder': preview_object['placeholder'],
        'теги': preview_object['теги'],
        'описание': preview_object['описание']
    }
    
    # Специальная обработка для колонки 'key'
    if selected_column == 'key':
        if is_new_column:
            st.info("🔑 Создание новой колонки 'key' - это заменит существующую!")
            st.warning("⚠️ Внимание: При создании новой колонки 'key' старая будет перезаписана")
        else:
            st.error("❌ Колонка 'key' не может быть отредактирована!")
            st.info("💡 Для изменения колонки 'key' включите галочку 'Добавить новую колонку'")
            return False
    
    # Сохраняем в БД согласно логике из описание.cd
    if save_column_description(
        selected_data['database_name'],
        selected_data['schema_name'],
        selected_data['table_name'],
        selected_column,
        _new_object,
        is_new_column=is_new_column
    ):
        if selected_column == 'key':
            st.success(f"🔑 Колонка '{selected_column}' успешно {'создана' if is_new_column else 'обновлена'}!")
        else:
            st.success(f"Колонка '{selected_column}' успешно {'добавлена' if is_new_column else 'обновлена'}!")
        st.info("Обновите страницу для отображения изменений")
        st.rerun()
        return True
    else:
        st.error("Ошибка при сохранении изменений")
        return False

def handle_delete_column(selected_column, selected_data):
    """Обрабатывает удаление колонки"""
    # Специальная обработка для колонки 'key'
    if selected_column == 'key':
        st.error("❌ Колонка 'key' не может быть удалена!")
        st.info("🔑 Колонка 'key' является системной и обязательной для таблицы")
        return False
    
    if delete_column_description(
        selected_data['database_name'],
        selected_data['schema_name'],
        selected_data['table_name'],
        selected_column
    ):
        st.success(f"Поле '{selected_column}' успешно удалено!")
        st.info("Обновите страницу для отображения изменений")
        st.rerun()
        return True
    else:
        st.error("Ошибка при удалении поля")
        return False

def display_save_logic(selected_column, preview_object, is_new_column):
    """Отображает логику сохранения согласно описание.cd"""
    st.divider()
    st.subheader("📋 Логика сохранения согласно описание.cd")
    if is_new_column:
        st.info(f"""
        **Режим добавления (new_column = true):**
        - _dict_key = "{selected_column}" (ключ колонки)
        - Dict["{selected_column}"] = preview_object
        - Добавляется новая колонка в словарь
        """)
    else:
        st.info(f"""
        **Режим редактирования (new_column = false):**
        - _dict_key = "{selected_column}" (текущая колонка)
        - Dict["{selected_column}"] = preview_object
        - Изменяется существующая колонка в словаре
        """)

def create_new_column_form(selected_data):
    """Создает форму для добавления новой колонки"""
    st.subheader("➕ Добавить новую колонку")
    
    with st.form("add_new_column"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_column_name = st.text_input(
                "Название колонки *",
                help="Введите название новой колонки",
                key="new_column_name"
            )
            
            new_datatype = st.text_input(
                "Datatype *",
                help="Тип данных колонки (например: character varying, numeric, text)",
                key="new_column_datatype"
            )
            
            new_placeholder = st.text_input(
                "Placeholder",
                help="Пример значения для колонки",
                key="new_column_placeholder"
            )
        
        with col2:
            new_tags = st.text_input(
                "Теги (через запятую)",
                help="Теги для классификации колонки",
                key="new_column_tags"
            )
            
            new_description = st.text_area(
                "Описание *",
                help="Описание назначения колонки",
                key="new_column_description"
            )
        
        # Специальная обработка для колонки 'key'
        is_key_column = new_column_name == 'key' if new_column_name else False
        if is_key_column:
            st.warning("⚠️ Создание колонки 'key' заменит существующую!")
            st.info("🔑 Колонка 'key' является системной и будет перезаписана")
        
        # Кнопка добавления
        if st.form_submit_button("➕ Добавить колонку", use_container_width=True):
            if new_column_name and new_datatype and new_description:
                # Создаем объект для новой колонки
                new_column_data = {
                    'datatype': new_datatype,
                    'placeholder': new_placeholder,
                    'теги': [tag.strip() for tag in new_tags.split(',') if tag.strip()] if new_tags else [],
                    'описание': new_description
                }
                
                # Сохраняем новую колонку
                if save_column_description(
                    selected_data['database_name'],
                    selected_data['schema_name'],
                    selected_data['table_name'],
                    new_column_name,
                    new_column_data,
                    is_new_column=True
                ):
                    st.success(f"✅ Колонка '{new_column_name}' успешно добавлена!")
                    st.info("🔄 Обновите страницу для отображения изменений")
                    st.rerun()
                else:
                    st.error(f"❌ Ошибка при добавлении колонки '{new_column_name}'")
            else:
                st.error("❌ Заполните обязательные поля (название, тип данных, описание)")

# =============================================================================
# СИСТЕМА АВТОРИЗАЦИИ
# =============================================================================

def check_authentication():
    """Проверяет авторизацию пользователя"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    return st.session_state.authenticated

def login_page():
    """Страница входа в систему"""
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        color: white;
        font-size: 2.5rem;
        margin-bottom: 2rem;
    }
    .login-container {
        background-color: #262730;
        border-radius: 10px;
        padding: 2rem;
        margin: 2rem auto;
        max-width: 500px;
        border: 1px solid #4a4a4a;
    }
    .form-label {
        color: white;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
        display: block;
    }
    .form-input {
        background-color: #4a4a4a;
        border: none;
        border-radius: 5px;
        padding: 0.75rem;
        color: white;
        width: 100%;
        margin-bottom: 1rem;
    }
    .login-button {
        background-color: #4a4a4a;
        border: 1px solid white;
        border-radius: 5px;
        padding: 0.75rem 2rem;
        color: white;
        cursor: pointer;
        width: 100%;
        font-size: 1.1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">🔐 Админ Панель</h1>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        st.markdown('<h2 style="text-align: center; color: white; margin-bottom: 2rem;">Вход в систему</h2>', unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("👤 Имя пользователя", key="login_username_input")
            password = st.text_input("🔒 Пароль", type="password", key="login_password_input")
            
            if st.form_submit_button("🚀 Войти", use_container_width=True):
                if authenticate_user(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.success("✅ Успешная авторизация!")
                    st.rerun()
                else:
                    st.error("❌ Неверное имя пользователя или пароль")
        
        
        
        st.markdown('</div>', unsafe_allow_html=True)

def authenticate_user(username, password):
    """Аутентификация пользователя из БД или переменных окружения"""
    # Инициализируем системных пользователей в начале функции
    valid_users = {
        "admin": os.getenv('ADMIN_PASSWORD', 'admin123'),
        "user": os.getenv('USER_PASSWORD', 'user123'),
        "test": os.getenv('TEST_PASSWORD', 'test123')
    }
    
    try:
        # Сначала проверяем пользователей из БД
        engine = get_sqlalchemy_engine()
        
        # Проверяем существование таблицы user_backup
        check_table_query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'user_backup'
            );
        """)
        
        with engine.connect() as conn:
            result = conn.execute(check_table_query)
            table_exists = result.scalar()
            
            if table_exists:
                # Ищем пользователя в БД
                user_query = text("""
                    SELECT hashed_password FROM user_backup 
                    WHERE username = :username AND is_active = true
                """)
                
                result = conn.execute(user_query, {'username': username})
                row = result.fetchone()
                
                if row:
                    # Проверяем пароль
                    from werkzeug.security import check_password_hash
                    hashed_password = row[0]
                    
                    if check_password_hash(hashed_password, password):
                        logging.info(f'Успешная авторизация пользователя {username} из БД')
                        return True
                    else:
                        logging.warning(f'Неверный пароль для пользователя {username} из БД')
                        return False
        
        # Если пользователь не найден в БД, проверяем системных пользователей
        
        is_valid = username in valid_users and valid_users[username] == password
        
        if is_valid:
            logging.info(f'Успешная авторизация системного пользователя: {username}')
        else:
            logging.warning(f'Неудачная попытка авторизации для пользователя: {username}')
        
        return is_valid
        
    except Exception as e:
        logging.error(f'Ошибка при аутентификации пользователя {username}: {e}', exc_info=True)
        
        # Fallback к системным пользователям при ошибке БД
        is_valid = username in valid_users and valid_users[username] == password
        
        if is_valid:
            logging.info(f'Успешная авторизация системного пользователя {username} (fallback)')
        else:
            logging.warning(f'Неудачная попытка авторизации для пользователя {username} (fallback)')
        
        return is_valid

def get_user_role(username):
    """Получить роль пользователя из БД или системных настроек"""
    try:
        # Сначала проверяем пользователей из БД
        engine = get_sqlalchemy_engine()
        
        # Проверяем существование таблицы user_backup
        check_table_query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'user_backup'
            );
        """)
        
        with engine.connect() as conn:
            result = conn.execute(check_table_query)
            table_exists = result.scalar()
            
            if table_exists:
                # Ищем пользователя в БД
                user_query = text("""
                    SELECT full_name FROM user_backup 
                    WHERE username = :username AND is_active = true
                """)
                
                result = conn.execute(user_query, {'username': username})
                row = result.fetchone()
                
                if row:
                    full_name = row[0]
                    if full_name:
                        return f"Пользователь ({full_name})"
                    else:
                        return "Пользователь"
        
        # Если пользователь не найден в БД, проверяем системных пользователей
        user_roles = {
            "admin": "Администратор",
            "user": "Пользователь", 
            "test": "Тестовый"
        }
        return user_roles.get(username, "Неизвестно")
        
    except Exception as e:
        logging.error(f'Ошибка при получении роли пользователя {username}: {e}', exc_info=True)
        
        # Fallback к системным ролям при ошибке БД
        user_roles = {
            "admin": "Администратор",
            "user": "Пользователь", 
            "test": "Тестовый"
        }
        return user_roles.get(username, "Неизвестно")

def change_password(username, old_password, new_password):
    """Изменение пароля пользователя"""
    if authenticate_user(username, old_password):
        # В реальном приложении здесь должна быть логика сохранения в БД
        logging.info(f'Пользователь {username} изменил пароль')
        return True
    else:
        logging.warning(f'Попытка изменения пароля для пользователя {username} с неверным текущим паролем')
        return False

def add_user_to_backup(username, password, role, full_name="", email="", telegram_id="", telegram_username=""):
    """
    Добавляет нового пользователя в таблицу user_backup
    
    Args:
        username: имя пользователя
        password: пароль (будет захеширован)
        role: роль пользователя
        full_name: полное имя (опционально)
        email: email (опционально)
        telegram_id: ID в Telegram (опционально)
        telegram_username: username в Telegram (опционально)
    
    Returns:
        bool: True если пользователь успешно добавлен, False в случае ошибки
    """
    try:
        from datetime import datetime
        from werkzeug.security import generate_password_hash
        
        engine = get_sqlalchemy_engine()
        
        # Проверяем существование таблицы user_backup
        check_table_query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'user_backup'
            );
        """)
        
        with engine.connect() as conn:
            result = conn.execute(check_table_query)
            table_exists = result.scalar()
            
            if not table_exists:
                logging.error('Таблица user_backup не существует')
                return False
        
        # Хешируем пароль
        hashed_password = generate_password_hash(password)
        
        # Текущее время
        current_time = datetime.now()
        
        # SQL запрос для вставки
        insert_query = text("""
            INSERT INTO user_backup (
                username, email, full_name, hashed_password, 
                telegram_id, telegram_username, is_active, 
                created_at, updated_at
            ) VALUES (
                :username, :email, :full_name, :hashed_password,
                :telegram_id, :telegram_username, :is_active,
                :created_at, :updated_at
            )
        """)
        
        # Параметры для вставки
        params = {
            'username': username,
            'email': email or None,
            'full_name': full_name or None,
            'hashed_password': hashed_password,
            'telegram_id': telegram_id or None,
            'telegram_username': telegram_username or None,
            'is_active': True,  # Используем boolean вместо UUID
            'created_at': current_time,
            'updated_at': current_time
        }
        
        with engine.connect() as conn:
            result = conn.execute(insert_query, params)
            conn.commit()
        
        logging.info(f'Пользователь {username} успешно добавлен в таблицу user_backup')
        return True
        
    except Exception as e:
        logging.error(f'Ошибка при добавлении пользователя {username}: {e}', exc_info=True)
        return False

def get_users_from_backup():
    """
    Получает список пользователей из таблицы user_backup
    
    Returns:
        pd.DataFrame: DataFrame с пользователями или пустой DataFrame в случае ошибки
    """
    try:
        engine = get_sqlalchemy_engine()
        
        # Проверяем существование таблицы user_backup
        check_table_query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'user_backup'
            );
        """)
        
        with engine.connect() as conn:
            result = conn.execute(check_table_query)
            table_exists = result.scalar()
            
            if not table_exists:
                logging.warning('Таблица user_backup не существует')
                return pd.DataFrame()
        
        query = text("SELECT username, email, full_name, is_active, created_at, updated_at FROM user_backup ORDER BY created_at DESC")
        
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        
        return df
        
    except Exception as e:
        logging.error(f'Ошибка при получении пользователей: {e}', exc_info=True)
        return pd.DataFrame()

def delete_user_from_backup(username):
    """
    Удаляет пользователя из таблицы user_backup
    
    Args:
        username: имя пользователя для удаления
    
    Returns:
        bool: True если пользователь успешно удален, False в случае ошибки
    """
    try:
        # Нельзя удалить системных пользователей
        if username in ['admin', 'user', 'test']:
            logging.warning(f'Попытка удалить системного пользователя: {username}')
            return False
        
        engine = get_sqlalchemy_engine()
        
        # Проверяем существование таблицы user_backup
        check_table_query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'user_backup'
            );
        """)
        
        with engine.connect() as conn:
            result = conn.execute(check_table_query)
            table_exists = result.scalar()
            
            if not table_exists:
                logging.error('Таблица user_backup не существует')
                return False
            
            # Удаляем пользователя
            delete_query = text("DELETE FROM user_backup WHERE username = :username")
            result = conn.execute(delete_query, {'username': username})
            conn.commit()
            
            if result.rowcount > 0:
                logging.info(f'Пользователь {username} успешно удален из таблицы user_backup')
                return True
            else:
                logging.warning(f'Пользователь {username} не найден в таблице user_backup')
                return False
        
    except Exception as e:
        logging.error(f'Ошибка при удалении пользователя {username}: {e}', exc_info=True)
        return False

def logout_button():
    """Кнопка выхода из системы"""
    if st.sidebar.button("🚪 Выйти", key="sidebar_logout_btn"):
        username = st.session_state.get('username', 'Неизвестно')
        logging.info(f'Пользователь {username} вышел из системы')
        st.session_state.authenticated = False
        st.session_state.username = None
        st.rerun()

# =============================================================================
# ОСНОВНОЙ КОД
# =============================================================================

# Проверяем авторизацию
if not check_authentication():
    login_page()
    st.stop()

# Показываем информацию о пользователе и кнопку выхода
st.sidebar.success(f"👤 {st.session_state.username}")
st.sidebar.info(f"🎭 Роль: {get_user_role(st.session_state.username)}")

# Показываем права доступа
if st.session_state.get('username') == 'user':
    st.sidebar.info("📝 Доступ к просмотру, редактированию и добавлению")
elif st.session_state.get('username') == 'test':
    st.sidebar.warning("👀 Только просмотр")

# Разделитель
st.sidebar.divider()

# Форма изменения пароля
with st.sidebar.expander("🔐 Изменить пароль"):
    with st.form("change_password_form"):
        old_password = st.text_input("🔒 Текущий пароль", type="password", key="sidebar_old_password")
        new_password = st.text_input("🔑 Новый пароль", type="password", key="sidebar_new_password")
        confirm_password = st.text_input("✅ Подтвердите пароль", type="password", key="sidebar_confirm_password")
        
        if st.form_submit_button("🔄 Изменить пароль", use_container_width=True):
            if new_password == confirm_password and new_password:
                if change_password(st.session_state.username, old_password, new_password):
                    st.success("✅ Пароль успешно изменен!")
                else:
                    st.error("❌ Неверный текущий пароль!")
            else:
                st.error("❌ Пароли не совпадают или пустые!")

logout_button()

# Инициализация session_state
if 'confirm_delete' not in st.session_state:
    st.session_state.confirm_delete = False

if 'show_add_column_form' not in st.session_state:
    st.session_state.show_add_column_form = False

# Создаем вкладки для разных операций
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Просмотр","➕ Добавление", "✏️ Редактирование", "🗑️ Удаление", "👥 Пользователи"])

with tab1:
    st.header('Список записей')
    try:
        data = get_database_descriptions()
        if not data.empty:
            # Создаем список для выбора в формате database.schema.table
            data['display_name'] = data.apply(
                lambda row: f"{row['database_name']}.{row['schema_name']}.{row['table_name']}", 
                axis=1
            )
            
            # Переупорядочиваем столбцы, чтобы id был в конце
            if 'id' in data.columns:
                # Получаем все столбцы кроме id
                other_columns = [col for col in data.columns if col != 'id']
                # Добавляем id в конец
                reordered_columns = other_columns + ['id']
                # Переупорядочиваем DataFrame
                data = data[reordered_columns]
            
            st.dataframe(data, use_container_width=True)
            
            # Экспорт данных
            st.subheader("📤 Экспорт данных")
            
            # Функция для очистки данных перед экспортом
            def clean_data_for_export(df):
                """Очищает DataFrame от объектов, которые нельзя сериализовать в JSON"""
                cleaned_df = df.copy()
                
                for col in cleaned_df.columns:
                    if cleaned_df[col].dtype == 'object':
                        # Очищаем объекты Json и другие несериализуемые объекты
                        cleaned_df[col] = cleaned_df[col].apply(lambda x: 
                            str(x) if hasattr(x, '__str__') else x
                        )
                
                return cleaned_df
            
            # Очищаем данные для экспорта
            export_data = clean_data_for_export(data)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Экспорт в CSV
                csv_data = export_data.to_csv(index=False)
                st.download_button(
                    label="📥 Скачать CSV",
                    data=csv_data,
                    file_name=f"database_descriptions_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                # Экспорт в JSON
                try:
                    json_data = export_data.to_json(orient='records', indent=2)
                    st.download_button(
                        label="📥 Скачать JSON",
                        data=json_data,
                        file_name=f"database_descriptions_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                except Exception as e:
                    st.error(f"Ошибка при создании JSON: {e}")
                    st.info("Попробуйте экспорт в CSV или обратитесь к администратору")
        else:
            st.warning('Данные не загружены или таблица пуста')
    except Exception as e:
        st.error(f'Ошибка при загрузке данных: {e}')
        data = pd.DataFrame()

with tab2:
    st.header('➕ Добавление новой записи')
            
    # Форма добавления новой записи
    with st.form("add_new_record"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_database_name = st.text_input(
                "Database Name",
                placeholder="Введите название базы данных",
                help="Название базы данных",
                key="add_db_name"
            )
            
            new_schema_name = st.text_input(
                "Schema Name",
                placeholder="public",
                help="Название схемы (например: public)",
                key="add_schema_name"
            )
            
            new_table_name = st.text_input(
                "Table Name",
                placeholder="Введите название таблицы",
                help="Название таблицы",
                key="add_table_name"
            )
        
        with col2:
            new_object_type = st.selectbox(
                "Object Type",
                options=["table", "view", "function", "procedure", "trigger", "index"],
                help="Тип объекта в базе данных",
                key="add_object_type"
            )
            
            new_description = st.text_area(
                "Description",
                placeholder="Общее описание записи",
                help="Описание назначения и использования записи",
                key="add_description"
            )
        
        # Секция для table_description (JSON)
        st.subheader("📊 Table Description (JSON)")
        
        # Показываем пример правильного JSON
        st.info("""
        **Пример правильного JSON формата:**
        ```json
        {
          "cogs": {
            "datatype": "numeric",
            "placeholder": "100",
            "теги": ["товар", "себестоимость"],
            "описание": "себестоимость товара"
          },
          "row_sum": {
            "datatype": "numeric", 
            "placeholder": "500",
            "теги": ["товар", "сумма"],
            "описание": "сумма товара"
          }
        }
        ```
        """)
        
        new_table_description = st.text_area(
            "Table Description (JSON)",
            help="Введите JSON описание колонок таблицы. Оставьте пустым, если не нужно описание колонок.",
            height=200,
            placeholder='{"column_name": {"datatype": "type", "placeholder": "example", "теги": ["tag1"], "описание": "desc"}}',
            key="add_table_description"
        )
        
        # Кнопка добавления (только для администраторов и пользователей)
        if st.form_submit_button("➕ Добавить запись в БД"):
            # Проверяем права доступа
            current_user = st.session_state.get('username')
            if current_user not in ['admin', 'user']:
                st.error("❌ Недостаточно прав для добавления записей")
                st.info("💡 Только администраторы и пользователи могут добавлять записи")
                st.stop()
            if new_database_name and new_schema_name and new_table_name:
                try:
                    # Проверяем подключение к БД
                    try:
                        engine = get_sqlalchemy_engine()
                        with engine.connect() as conn:
                            st.success("✅ Подключение к БД успешно")
                    except Exception as db_error:
                        st.error(f"❌ Ошибка подключения к БД: {db_error}")
                        st.stop()
                    
                    # Парсим JSON table_description
                    table_desc_json = {}
                    if new_table_description.strip():
                        try:
                            table_desc_json = json.loads(new_table_description)
                            st.success("✅ JSON успешно распарсен")
                        except json.JSONDecodeError as e:
                            st.error(f"❌ Ошибка в JSON формате: {e}")
                            st.info("""
                            **Проверьте синтаксис JSON:**
                            - Все строки должны быть в кавычках
                            - Элементы в массивах разделяются запятыми
                            - Последний элемент не должен иметь запятую
                            - Проверьте скобки и кавычки
                            """)
                            st.code(new_table_description, language="text")
                            st.stop()
                        else:
                            # Создаем новую запись
                            st.info("🔄 Создание записи в БД...")
                            if add_new_record(
                                new_database_name,
                                new_schema_name,
                                new_table_name,
                                new_object_type,
                                new_description,
                                table_desc_json
                            ):
                                st.success(f"✅ Запись '{new_database_name}.{new_schema_name}.{new_table_name}' успешно добавлена в БД!")
                                st.info("Обновите страницу для отображения изменений")
                                st.rerun()
                            else:
                                st.error("❌ Ошибка при добавлении записи в БД")
                                st.info("Проверьте логи для деталей ошибки")
                    else:
                        # Если JSON пустой, создаем запись с пустым table_description
                        st.info("🔄 Создание записи с пустым table_description...")
                        if add_new_record(
                            new_database_name,
                            new_schema_name,
                            new_table_name,
                            new_object_type,
                            new_description,
                            {}
                        ):
                            st.success(f"✅ Запись '{new_database_name}.{new_schema_name}.{new_table_name}' успешно добавлена в БД!")
                            st.info("Обновите страницу для отображения изменений")
                            st.rerun()
                        else:
                            st.error("❌ Ошибка при добавлении записи в БД")
                            st.info("Проверьте логи для деталей ошибки")
                except Exception as e:
                    st.error(f"❌ Неожиданная ошибка: {e}")
                    st.info("Проверьте логи для деталей ошибки")
        else:
            st.error("❌ Database Name, Schema Name и Table Name обязательны!")

with tab3:
    st.header('✏️ Редактирование')
    
    if 'data' in locals() and not data.empty:
        # Выбор записи для редактирования
        selected_record = st.selectbox(
            "Выберите строку из списка:",
            options=data['display_name'].tolist(),
            help="Имя в списке выглядит так: database_name.schema_name.table_name",
            key="edit_record_select"
        )
        
        if selected_record:
            # Находим выбранную запись
            selected_data = data[data['display_name'] == selected_record].iloc[0]
            
            # Показываем описание колонок
            if selected_data.get('table_description'):
                try:
                    table_desc1 = selected_data['table_description']
                    table_desc = table_desc1.get('columns', {})
                    logging.info(f'table_desc: {table_desc}')
                    logging.info(f'table_desc1: {table_desc1}')
                    
                    # Автоматически создаем поле 'key' если его нет
                    if isinstance(table_desc, dict) and 'key' not in table_desc and len(table_desc) > 0:
                        # Создаем поле 'key' на основе bill_key или первой колонки
                        if 'bill_key' in table_desc:
                            # Используем bill_key как основу для key
                            key_data = table_desc['bill_key'].copy() if isinstance(table_desc['bill_key'], dict) else {}
                            key_data['описание'] = 'Основной ключ таблицы (автоматически создан)'
                            key_data['теги'] = ['ключ', 'основной', 'автоматический']
                            table_desc['key'] = key_data
                        else:
                            # Создаем базовое поле 'key'
                            first_col = list(table_desc.keys())[0]
                            first_col_data = table_desc[first_col] if isinstance(table_desc[first_col], dict) else {}
                            table_desc['key'] = {
                                'datatype': 'character varying',
                                'placeholder': 'primary_key',
                                'теги': ['ключ', 'основной', 'автоматический'],
                                'описание': 'Основной ключ таблицы (автоматически создан)'
                            }
                            
                                                
                    
                                        # Проверяем тип данных и парсим JSON если нужно
                    if isinstance(table_desc, str):
                        try:
                            table_desc = json.loads(table_desc)
                        except json.JSONDecodeError:
                            st.error("Ошибка при парсинге JSON описания колонок")
                            table_desc = {}
                    elif table_desc is None:
                        table_desc = {}
                    
                    # Проверяем, что table_desc это словарь
                    if not isinstance(table_desc, dict):
                        st.error(f"Неожиданный тип данных для table_description: {type(table_desc)}")
                        table_desc = {}
                    
                    if table_desc:
                        # Создаем DataFrame для отображения колонок
                        columns_df = create_column_dataframe(table_desc)
                        
                        if columns_df is not None:
                            # Показываем колонки
                            st.subheader("КОЛОНКИ:")
                            st.dataframe(columns_df, use_container_width=True)
                            
                            st.divider()
                            
                            # Кнопка для добавления новой колонки
                            col1, col2 = st.columns([1, 3])
                            with col1:
                                if st.button("➕ Добавить колонку", type="primary", key="add_column_btn"):
                                    st.session_state.show_add_column_form = True
                            
                            with col2:
                                if st.session_state.get('show_add_column_form', False):
                                    st.info("📝 Заполните форму ниже для добавления новой колонки")
                            
                            # Показываем форму добавления новой колонки
                            if st.session_state.get('show_add_column_form', False):
                                create_new_column_form(selected_data)
                                st.divider()
                            
                            # Выбор колонки для редактирования
                            selected_column = st.selectbox(
                                "Выберите колонку для редактирования:",
                                options=columns_df['Колонка'].tolist(),
                                help="Выберите колонку для редактирования или добавления",
                                key="edit_column_select"
                            )
                            
                            if selected_column:
                                st.subheader(f"✏️ Редактирование колонки: {selected_column}")
                                
                                # Проверяем, можно ли редактировать это поле
                                if selected_column == 'id':
                                    st.error("❌ Поле 'id' недоступно для редактирования!")
                                    st.info("ID записи является системным полем и не может быть изменен")
                                else:
                                    # Получаем текущие данные колонки
                                    current_col_info = table_desc.get(selected_column, {})
                                    if not isinstance(current_col_info, dict):
                                        current_col_info = {}
                                    
                                    # Создаем форму редактирования
                                    create_edit_form(selected_column, current_col_info, selected_data)
                        else:
                            st.info("В описании полей нет данных")
                    else:
                        st.info("Описание полей пустое")
                        
                except Exception as e:
                    st.error(f"Ошибка при обработке описания полей: {e}")
                    st.info("Попробуйте обновить страницу или обратитесь к администратору")
            else:
                st.info("Описание полей отсутствует")
        else:
            st.warning('Данные не загружены или таблица пуста')
        

with tab4:
    st.header('🗑️ Удаление')
    
    if 'data' in locals() and not data.empty:
        # Выбор записи для удаления
        selected_record = st.selectbox(
            "Выберите запись для удаления:",
            options=data['display_name'].tolist(),
            help="Выберите запись из списка для удаления",
            key="delete_record_select"
        )
        
        if selected_record:
            selected_data = data[data['display_name'] == selected_record].iloc[0]
            
            st.subheader(f"🗑️ Удаление записи: {selected_record}")
            
            # Показываем информацию о записи
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**База данных:** {selected_data['database_name']}")
                st.write(f"**Схема:** {selected_data['schema_name']}")
            with col2:
                st.write(f"**Таблица:** {selected_data['table_name']}")
                st.write(f"**ID:** {selected_data.get('id', 'N/A')}")
            
            # Разделитель
            st.divider()
            
            # Секция удаления записи
            st.subheader("🗑️ Удаление записи из БД")
            st.warning("⚠️ **Внимание!** Удаление записи приведет к полной потере всех данных, включая описания колонок.")
            
            # Кнопка удаления записи (только для администраторов)
            if st.session_state.get('username') == 'admin':
                if st.button("🗑️ УДАЛИТЬ ЗАПИСЬ ИЗ БД", type="primary", key="delete_record_btn"):
                    # Подтверждение удаления
                    if st.session_state.get('confirm_delete', False):
                        # Выполняем удаление
                        if delete_record(
                            selected_data['database_name'],
                            selected_data['schema_name'],
                            selected_data['table_name']
                        ):
                            st.success(f"✅ Запись '{selected_record}' успешно удалена из БД!")
                            st.info("Обновите страницу для отображения изменений")
                            # Сбрасываем флаг подтверждения
                            st.session_state.confirm_delete = False
                            st.rerun()
                        else:
                            st.error("❌ Ошибка при удалении записи из БД")
                    else:
                        # Запрашиваем подтверждение
                        st.session_state.confirm_delete = True
                        st.error("⚠️ Для подтверждения удаления нажмите кнопку еще раз!")
            else:
                st.warning("⚠️ Только администраторы могут удалять записи")
            
            # Показываем статус подтверждения
            if st.session_state.get('confirm_delete', False):
                st.info("🔄 Нажмите кнопку удаления еще раз для подтверждения")
            
            # Разделитель
            st.divider()

with tab5:
    st.header('👥 Управление пользователями')
    
    # Проверяем, является ли текущий пользователь администратором
    if st.session_state.get('username') == 'admin':
        st.success("🔐 Доступ к управлению пользователями разрешен")
        
        # Показываем текущих пользователей из таблицы user_backup
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader("📋 Список пользователей из БД")
        with col2:
            if st.button("🔄 Обновить", key="refresh_users_btn"):
                st.rerun()
        
        try:
            users_df = get_users_from_backup()
            if not users_df.empty:
                # Форматируем даты для лучшего отображения
                if 'created_at' in users_df.columns:
                    users_df['created_at'] = pd.to_datetime(users_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
                if 'updated_at' in users_df.columns:
                    users_df['updated_at'] = pd.to_datetime(users_df['updated_at']).dt.strftime('%Y-%m-%d %H:%M')
                
                st.dataframe(users_df, use_container_width=True)
                st.info(f"📊 Всего пользователей: {len(users_df)}")
                
                # Секция удаления пользователей
                st.divider()
                st.subheader("🗑️ Удаление пользователей")
                
                # Выбор пользователя для удаления
                usernames = users_df['username'].tolist()
                # Исключаем системных пользователей из списка удаления
                non_system_users = [u for u in usernames if u not in ['admin', 'user', 'test']]
                
                if non_system_users:
                    selected_user_to_delete = st.selectbox(
                        "Выберите пользователя для удаления:",
                        options=non_system_users,
                        help="Системные пользователи (admin, user, test) не могут быть удалены",
                        key="delete_user_select"
                    )
                    
                    if selected_user_to_delete:
                        st.warning(f"⚠️ Вы собираетесь удалить пользователя: **{selected_user_to_delete}**")
                        st.info("Это действие нельзя отменить!")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("🗑️ УДАЛИТЬ ПОЛЬЗОВАТЕЛЯ", type="primary", key=f"delete_user_{selected_user_to_delete}"):
                                if delete_user_from_backup(selected_user_to_delete):
                                    st.success(f"✅ Пользователь '{selected_user_to_delete}' успешно удален!")
                                    st.info("🔄 Обновите страницу для отображения изменений")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Ошибка при удалении пользователя '{selected_user_to_delete}'")
                        with col2:
                            if st.button("❌ Отмена", key=f"cancel_delete_{selected_user_to_delete}"):
                                st.rerun()
                else:
                    st.info("📝 Нет пользователей для удаления (только системные пользователи)")
                    
            else:
                st.info("📝 В таблице user_backup пока нет пользователей")
        except Exception as e:
            st.error(f"❌ Ошибка при загрузке пользователей: {e}")
            st.info("📝 Показываем базовый список пользователей")
            users_data = {
                "Имя пользователя": ["admin", "user", "test"],
                "Роль": ["Администратор", "Пользователь", "Тестовый"],
                "Пароль": [os.getenv('ADMIN_PASSWORD', 'admin123'), os.getenv('USER_PASSWORD', 'user123'), os.getenv('TEST_PASSWORD', 'test123')]
            }
            users_df = pd.DataFrame(users_data)
            st.dataframe(users_df, use_container_width=True)
        
        st.divider()
        
        # Форма добавления нового пользователя
        st.subheader("➕ Добавить нового пользователя")
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input("👤 Имя пользователя *", key="users_new_username")
                new_password = st.text_input("🔒 Пароль *", type="password", key="users_new_password")
                new_role = st.selectbox("🎭 Роль", ["Пользователь", "Администратор", "Тестовый"], key="users_new_role")
                full_name = st.text_input("👤 Полное имя", key="users_full_name")
            
            with col2:
                email = st.text_input("📧 Email", key="users_email")
                telegram_id = st.text_input("📱 Telegram ID", key="users_telegram_id")
                telegram_username = st.text_input("📱 Telegram Username", key="users_telegram_username")
            
            if st.form_submit_button("➕ Добавить пользователя", use_container_width=True):
                if new_username and new_password:
                    # Валидация email если указан
                    email_valid = True
                    if email and '@' not in email:
                        st.error("❌ Неверный формат email адреса!")
                        email_valid = False
                    
                    # Валидация Telegram ID если указан
                    telegram_valid = True
                    if telegram_id and not telegram_id.isdigit():
                        st.error("❌ Telegram ID должен содержать только цифры!")
                        telegram_valid = False
                    
                    # Добавляем пользователя только если все валидации пройдены
                    if email_valid and telegram_valid:
                        if add_user_to_backup(
                            username=new_username,
                            password=new_password,
                            role=new_role,
                            full_name=full_name,
                            email=email,
                            telegram_id=telegram_id,
                            telegram_username=telegram_username
                        ):
                            st.success(f"✅ Пользователь '{new_username}' успешно добавлен в таблицу user_backup!")
                            st.info("🔄 Обновите страницу для отображения изменений")
                            # Просто перезагружаем страницу - форма очистится автоматически
                            st.rerun()
                        else:
                            st.error("❌ Ошибка при добавлении пользователя в БД")
                else:
                    st.error("❌ Заполните обязательные поля (имя пользователя и пароль)!")
    else:
        st.warning("⚠️ Только администраторы могут управлять пользователями")
        st.info("👤 Текущий пользователь: " + st.session_state.get('username', 'Неизвестно'))


