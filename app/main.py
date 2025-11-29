from fastapi import FastAPI, HTTPException
from pathlib import Path
from dotenv import load_dotenv
import os
import asyncio

from qdrant_manager import QdrantReportsManager
from py_models import *

env_path = Path(__file__).resolve().parents[0] / ".env"
load_dotenv(dotenv_path=env_path)

if os.getenv('CURRENT_DEVICE') == "server":
    from llm import LLMReportGenerator
else:
    from llm_plug import LLMReportGenerator

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

@app.post("/qdrant", response_model=QdrantAddReportResponse)
async def qdrant_set_data(data: QdrantAddReportRequest) -> QdrantAddReportResponse:
    """Добавление отчёта в векторную БД"""
    qd_manager = QdrantReportsManager()
    result = qd_manager.add_report(data)
    return result

@app.get("/qdrant/reports", response_model=QdrantAllReportsResponse)
async def get_all_reports() -> QdrantAllReportsResponse:
    """Получение списка всех отчётов"""
    qd_manager = QdrantReportsManager()
    return qd_manager.get_all_reports()

@app.get("/qdrant/reports/{report_id}")
async def get_report_by_id(report_id: str):
    """Получение полных данных отчёта по ID"""
    qd_manager = QdrantReportsManager()
    report = qd_manager.get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Отчёт не найден")
    return report

@app.delete("/qdrant/reports/{report_id}", response_model=QdrantDeleteReportResponse)
async def delete_report(report_id: str) -> QdrantDeleteReportResponse:
    """Удаление отчёта по ID"""
    qd_manager = QdrantReportsManager()
    return qd_manager.delete_report(report_id)