from fastapi import FastAPI, HTTPException

from llm_plug import LLMReportGenerator
from qdrant_manager import QdrantReportsManager
from py_models import *
import asyncio

app = FastAPI(title="Heavy Class Demo")

@app.on_event("startup")
async def startup_event():
    """Инициализируем модель при запуске"""
    async def LLM_init() -> LLMReportGenerator:
        return LLMReportGenerator()
    async def qdrant_client_init() -> QdrantReportsManager:
        return QdrantReportsManager()
    
    print("🔄 Запуск приложения...")
    qdrantClient = qdrant_client_init()
    llm = LLM_init()
    qdrantClient = await qdrantClient
    qdrantClient.init_collection()
    llm = await llm
    print("✅ Приложение готово к работе")

@app.post("/generate_text")
async def generate_endpoint(user_request: str):
    result = LLMResponse()
    try:
        # Используем синглтон - всегда получаем тот же экземпляр
        llm = LLMReportGenerator()
        
        # Запускаем генерацию в отдельном потоке
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: llm.generate_response(user_request)
        )
        result.text = response
    except Exception as e:
        result.text = f"Ошибка генерации: {str(e)}"
    
    return result

@app.post("/qdrant")
async def qdrant_set_data(data: QdrantAddReportRequest) -> QdrantAddReportResponse:
    qd_manager = QdrantReportsManager()
    result = qd_manager.add_report(data)
    return result