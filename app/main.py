from fastapi import FastAPI, HTTPException, Depends
from pathlib import Path
from dotenv import load_dotenv
import os
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from qdrant_manager import QdrantReportsManager
from py_models import *
from db.requests import *
from db.connect_db import get_async_session
from promt import generate_promt

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
    llm = LLM_init()
    if os.getenv('CURRENT_DEVICE') == "server":
        qdrantClient = qdrant_client_init()
        qdrantClient = await qdrantClient
        qdrantClient.init_collection()
    llm = await llm
    print("✅ Приложение готово к работе")

# Генерируем текст
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

# Взаимодействие с qdrant
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

@app.post("/qdrant/reports/distance")
async def get_distance(report1_id: str, report2_id: str, section_code: str) -> QdrantReportSectionsComparison:
    
    qd_manager = QdrantReportsManager()
    return qd_manager.compare_single_section_pair(report1_id, report2_id, section_code)

# Запросы в БД !!!ТЕСТОВОЕ!!!
@app.post("/db/test/query/all")
async def test_querry(section_num: int, table_num, session: AsyncSession = Depends(get_async_session)) -> dict:
    match section_num:
        case 1:
            manager = RequestsForFirstSection(year=2025, exam_type_id=4, subject_id=2, start_date="2024-05-27", end_date="2024-07-04")
            match table_num:
                case 1:
                    result = await manager.getTable_areas(session)
                case 2:
                    result = await manager.getTable_schoolKinds(session)
                case 3:
                    result = await manager.getTable_categories(session)
                case 4:
                    result = await manager.getTable_sex(session)
                case 5:
                    result = await manager.getTable_count(session)
                case 6:
                    result = await manager.getTable_profBaseMat(session)
        case 2:
            manager = RequestsForSecondSection(year=2025, exam_type_id=4, subject_id=2, start_date="2024-05-27", end_date="2024-07-04")
            match table_num:
                case 1:
                    result = await manager.getTable_scoreDictribution(session)
                case 2:
                    result = await manager.getTable_resultDynamic(session)
                case 3:
                    result = await manager.getTable_resultByStudCat(session)
                case 4:
                    result = await manager.getTable_resultBySchoolTypes(session)
                case 5:
                    result = await manager.getTable_resultBySex(session)
                case 6:
                    result = await manager.getTable_resultByAreas(session)
                case 7:
                    result = await manager.getTable_lowResults(session)
    
    return {
        "status": "correct",
        "data": result
    }

# Формирование первого раздела
@app.get("/report/generate/section/one")
async def generate_section_one(session: AsyncSession = Depends(get_async_session)):
    
    promt = await generate_promt(session=session, section_number=1)
    
    print('*'*100)
    with open ('promt.txt', 'w') as f:
        f.write(promt)
    print('='*100)
    
    # Генерируем ответ
    result = LLMResponse()
    try:
        # Используем синглтон - всегда получаем тот же экземпляр
        llm = LLMReportGenerator()
        
        # Запускаем генерацию в отдельном потоке
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: llm.generate_response(promt)
        )
        result.text = response["response"]
        result.time = response["time"]
    except Exception as e:
        result.text = f"Ошибка генерации: {str(e)}"
    
    return result

# Формирование второго раздела
@app.get("/report/generate/section/two")
async def generate_section_one(session: AsyncSession = Depends(get_async_session)):
    
    promt = await generate_promt(session=session, section_number=2)
    
    print('*'*100)
    with open ('promt.txt', 'w') as f:
        f.write(promt)
    print('='*100)
    
    # Генерируем ответ
    result = LLMResponse()
    try:
        # Используем синглтон - всегда получаем тот же экземпляр
        llm = LLMReportGenerator()
        
        # Запускаем генерацию в отдельном потоке
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: llm.generate_response(promt)
        )
        result.text = response["response"]
        result.time = response["time"]
    except Exception as e:
        result.text = f"Ошибка генерации: {str(e)}"
    
    return result