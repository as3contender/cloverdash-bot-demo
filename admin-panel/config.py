import os
from dotenv import load_dotenv

# агружаем .env файл
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)

# онфигурация базы данных
DB_CONFIG = {
    'host': os.getenv('APP_DATABASE_HOST', 'localhost'),
    'port': int(os.getenv('APP_DATABASE_PORT', '5432')),
    'user': os.getenv('APP_DATABASE_USER', 'postgres'),
    'password': os.getenv('APP_DATABASE_PASSWORD', ''),
    'database': os.getenv('APP_DATABASE_NAME', 'postgres')
}

def get_db_url():
    return 'postgresql+psycopg2://postgres:password@localhost:5432/postgres'
