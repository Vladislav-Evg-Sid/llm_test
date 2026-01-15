from fastapi import FastAPI
import os

from app.storage.qdrant.qdrant_manager import QdrantReportsStorage
from app.api import qdrant, text_reports

if os.getenv('CURRENT_DEVICE') == "server":
    from app.services.llm import LLMService
else:
    from app.services.llm_plug import LLMService

app = FastAPI(title="Heavy Class Demo")

app.include_router(qdrant.router)
app.include_router(text_reports.router)

@app.on_event("startup")
async def startup_event():
    """Инициализируем модель при запуске"""
    async def LLM_init() -> LLMService:
        return LLMService()
    async def qdrant_client_init() -> QdrantReportsStorage:
        return QdrantReportsStorage()
    
    print("🔄 Запуск приложения...")
    llm = await LLM_init()
    if os.getenv('CURRENT_DEVICE') == "server":
        qdrantClient = await qdrant_client_init()
        qdrantClient.init_collection()
    print("✅ Приложение готово к работе")
