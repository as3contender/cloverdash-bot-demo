from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv
import openai
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import asyncpg
import json

load_dotenv()

app = FastAPI(title="CloverdashBot Backend", version="1.0.0")


# Pydantic models for request/response
class QueryRequest(BaseModel):
    question: str
    user_id: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    sql_query: Optional[str] = None
    success: bool


# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/database")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI
openai.api_key = OPENAI_API_KEY
llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")

# Database schema context - будет расширяться
DB_SCHEMA_CONTEXT = """
Доступные таблицы и колонки в базе данных:
(Здесь будет описание схемы базы данных)
"""


@app.get("/")
async def root():
    return {"message": "CloverdashBot Backend API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Обрабатывает вопрос пользователя, создает SQL запрос с помощью LLM
    и возвращает результат из базы данных
    """
    try:
        # Создаем промпт для LLM
        system_prompt = f"""
        Ты - эксперт по SQL запросам. Твоя задача - создать SQL запрос на основе вопроса пользователя.
        
        Контекст базы данных:
        {DB_SCHEMA_CONTEXT}
        
        Правила:
        1. Возвращай только SQL запрос, без дополнительного текста
        2. Используй только SELECT запросы
        3. Запрос должен быть безопасным и не содержать потенциально вредоносного кода
        """

        human_prompt = f"Вопрос пользователя: {request.question}"

        # Получаем SQL запрос от LLM
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)]

        response = llm(messages)
        sql_query = response.content.strip()

        # Выполняем запрос к базе данных
        # TODO: Реализовать подключение к базе данных
        # conn = await asyncpg.connect(DATABASE_URL)
        # result = await conn.fetch(sql_query)
        # await conn.close()

        # Временная заглушка
        result = f"Результат выполнения запроса: {sql_query}"

        return QueryResponse(answer=result, sql_query=sql_query, success=True)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки запроса: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
