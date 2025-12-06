from fastapi import FastAPI, HTTPException, Depends
from pathlib import Path
from dotenv import load_dotenv
import os
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from qdrant_manager import QdrantReportsManager
from py_models import *
from db.requests import RequestsForFirstSection
from db.connect_db import get_async_session

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

# Запросы в БД !!!ТЕСТОВОЕ!!!
@app.get("/db/test/query/count")
async def test_querry(session: AsyncSession = Depends(get_async_session)) -> dict:
    try:
        manager = RequestsForFirstSection(year=2025, exam_type_id=4, subject_id=2, start_date="2024-05-27", end_date="2024-07-04")
        result = await manager.getTable_count(session)
        return {
            "status": "correct",
            "data": result
        }
    except Exception as e:
        return {
            "status": "error",
            "exception": e 
        }

@app.get("/db/test/query/sex")
async def test_querry(session: AsyncSession = Depends(get_async_session)) -> dict:
    manager = RequestsForFirstSection(year=2025, exam_type_id=4, subject_id=2, start_date="2024-05-27", end_date="2024-07-04")
    result = await manager.getTable_sex(session)
    return {
        "status": "correct",
        "data": result
    }

@app.get("/db/test/query/categories")
async def test_querry(session: AsyncSession = Depends(get_async_session)) -> dict:
    manager = RequestsForFirstSection(year=2025, exam_type_id=4, subject_id=2, start_date="2024-05-27", end_date="2024-07-04")
    result = await manager.getTable_categories(session)
    return {
        "status": "correct",
        "data": result
    }

@app.get("/db/test/query/schoolKinds")
async def test_querry(session: AsyncSession = Depends(get_async_session)) -> dict:
    manager = RequestsForFirstSection(year=2025, exam_type_id=4, subject_id=2, start_date="2024-05-27", end_date="2024-07-04")
    result = await manager.getTable_schoolKinds(session)
    return {
        "status": "correct",
        "data": result
    }

@app.get("/db/test/query/areas")
async def test_querry(session: AsyncSession = Depends(get_async_session)) -> dict:
    manager = RequestsForFirstSection(year=2025, exam_type_id=4, subject_id=2, start_date="2024-05-27", end_date="2024-07-04")
    result = await manager.getTable_areas(session)
    return {
        "status": "correct",
        "data": result
    }

# Формирование первого раздела
@app.get("/report/generate/section/one")
async def generate_section_one(session: AsyncSession = Depends(get_async_session)):
    manager = RequestsForFirstSection(year=2025, exam_type_id=4, subject_id=2, start_date="2024-05-27", end_date="2024-07-04")
    corutine_tableCount = manager.getTable_count(session)
    corutine_tableSex = manager.getTable_sex(session)
    corutine_tableCategories = manager.getTable_categories(session)
    corutine_tableSchools = manager.getTable_schoolKinds(session)
    corutine_tableAreas = manager.getTable_areas(session)
    
    promt = """Действуй как председатель предметной комиссии по учебной дисциплине "Математика профильная".
Твоя задача - составить раздел для отчёта, содержащий выводы о характере изменения количества участников ЕГЭ по профильной математике.
Делай выводы исходя из следующих данных:
1. Количество участников ЕГЭ по учебному предмету за 3 года:"""
    tableCount = await corutine_tableCount
    for i in range(3):
        promt += f"\n1.{i+1}. {tableCount.years[i]} год:\n1.{i+1}.1. Количество: {tableCount.counts[i]}.\n1.{i+1}.2. Процент от общего чесла участников по всем прдметам: {tableCount.procents[i]}."
    
    promt += "\n\n2. Процентное соотношение юношей и девушек, учавствовавших в ЕГЭ за 3 года:\n"
    tableSex = await corutine_tableSex
    for i in range(len(tableSex.category)):
        promt += f"""2.{i+1}. Пол: {tableSex.category[0]}:
2.{i+1}.1. Год: {tableSex.col_1[0][0]}.\n2.{i+1}.1.1. Количество: {tableSex.col_1[0][1]}.\n2.{i+1}.1.2. Процент от общего чесла участников по всем прдметам: {tableSex.col_1[0][2]} %.
2.{i+1}.2. Год: {tableSex.col_2[0][0]}.\n2.{i+1}.2.1. Количество: {tableSex.col_2[0][1]}.\n2.{i+1}.2.2. Процент от общего чесла участников по всем прдметам: {tableSex.col_2[0][2]} %.
2.{i+1}.3. Год: {tableSex.col_3[0][0]}.\n2.{i+1}.3.1. Количество: {tableSex.col_3[0][1]}.\n2.{i+1}.3.2. Процент от общего чесла участников по всем прдметам: {tableSex.col_3[0][2]} %.\n"""
    
    promt += "\n3. Количество участников экзамена в регионе по категориям за 3 года:\n"
    tableCategories = await corutine_tableCategories
    for i in range(len(tableCategories.category)):
        promt += f"""3.{i+1}. Категория: {tableCategories.category[0]}:
3.{i+1}.1. Год: {tableCategories.col_1[0][0]}.\n3.{i+1}.1.1. Количество: {tableCategories.col_1[0][1]}.\n3.{i+1}.1.2. Процент от общего чесла участников по всем прдметам: {tableCategories.col_1[0][2]} %.
3.{i+1}.2. Год: {tableCategories.col_2[0][0]}.\n3.{i+1}.2.1. Количество: {tableCategories.col_2[0][1]}.\n3.{i+1}.2.2. Процент от общего чесла участников по всем прдметам: {tableCategories.col_2[0][2]} %.
3.{i+1}.3. Год: {tableCategories.col_3[0][0]}.\n3.{i+1}.3.1. Количество: {tableCategories.col_3[0][1]}.\n3.{i+1}.3.2. Процент от общего чесла участников по всем прдметам: {tableCategories.col_3[0][2]} %.\n"""
    
    promt += "\n4. Количество участников экзамена в регионе по типам ОО за 3 года:\n"
    tableSchools = await corutine_tableSchools
    for i in range(len(tableSchools.category)):
        promt += f"""4.{i+1}. Тип образовательной организации: {tableSchools.category[0]}:
4.{i+1}.1. Год: {tableSchools.col_1[0][0]}.\n4.{i+1}.1.1. Количество: {tableSchools.col_1[0][1]}.\n4.{i+1}.1.2. Процент от общего чесла участников по всем прдметам: {tableSchools.col_1[0][2]} %.
4.{i+1}.2. Год: {tableSchools.col_2[0][0]}.\n4.{i+1}.2.1. Количество: {tableSchools.col_2[0][1]}.\n4.{i+1}.2.2. Процент от общего чесла участников по всем прдметам: {tableSchools.col_2[0][2]} %.
4.{i+1}.3. Год: {tableSchools.col_3[0][0]}.\n4.{i+1}.3.1. Количество: {tableSchools.col_3[0][1]}.\n4.{i+1}.3.2. Процент от общего чесла участников по всем прдметам: {tableSchools.col_3[0][2]} %.\n"""
    
    promt += "\n5. Количество участников ЕГЭ по учебному предмету по АТЕ региона:\n"
    tableAreas = await corutine_tableAreas
    for i in range(len(tableAreas.areas)):
        promt += f"""5.{i+1}. Наитемнование АТЕ: {tableAreas.areas[i]}
5.{i+1}.1. Количество участников по учебному предмету: {tableAreas.counts[i]}.
5.{i+1}.2. Процент от общего числа участников по всем предметам: {tableAreas.procents[i]}.\n"""
    
    promt += """
Используй в качестве примера выводы из отчёта за 2024 год, вот его текст:
<example>
Исходя из анализа количественного показателя по участникам в дисциплине «профильная математика в формате ЕГЭ» можно видеть стабильное уменьшение числа сдающих экзамен: по сравнению с 2022 годом «-320», с 2023 годом – «-140», причем стабильно падает показатель в СОШ, Гимназиях и Лицеях.
Основываясь на данной статистике и статистике по базовой математике, делаем вывод, что приоритет склоняется в пользу последней, базовой математике. Тут можно, на наш взгляд, указать следующие причины:
- с одной стороны, это определённая сложность в изучении математики на хорошем уровне, с другой стороны выпускниками школ делается выбор «по пути наименьшего сопротивления».
- увеличение количества бюджетных мест в ВУЗах, не требующих наличие профильной математики как вступительного экзамена.
- слабая развивающая работа ОО в младших классах и среднем звене (это не говоря уже и старшем звене), где вся работа сводится теперь только к положительному результату в написанию ВПР, так сказать, дрессировка, как в цирке, но там выполняют ту же программу, что и тренировали, а в образовании всё не так.
Ради справедливости, следует отметить, что осознанный выбор профильного экзамена учащимися, на протяжении вот уже нескольких лет, даёт свои результаты и это положительно отражается на качественном содержании проверяемых работ, т.е. пустых работ стало гораздо меньше.
<\example>

Не пытайся придумать, что будет выше или ниже данного раздела, не нужно оставлять место под подпись, подписываться или писать название раздела. Твоя задача - написать текст раздела, который будет вставлен в итоговый отчёт.

Председатель предметной комиссии: 
"""
    
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