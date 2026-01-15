from fastapi import APIRouter, Depends
import os
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

from app.schemas.text_reports import TableStandart, LLMResponse
from app.db.connect_db import get_async_session
from app.services.promt import get_report_generate_data
from app.services.table_rep_manager import get_table_by_section

if os.getenv('CURRENT_DEVICE') == "server":
    from app.services.llm import LLMService
else:
    from app.services.llm_plug import LLMService

router = APIRouter(
    prefix="/textreports",
    tags=["textreports"]
)


# Запросы в БД !!!ТЕСТОВОЕ!!!
@router.post("/db/test/query/all")
async def test_querry(section_num: int, table_num: int, session: AsyncSession = Depends(get_async_session)) -> TableStandart:
    return await get_table_by_section(session, section_num, table_num)

# Формирование первого раздела
@router.post("/report/generate/section")
async def generate_sections(section_code: str = "1.7.", session: AsyncSession = Depends(get_async_session)):
    data = await get_report_generate_data(session=session, section_code=section_code, exam_year=2025)
    
    with open ('promt.txt', 'w') as f:
        f.write(data.promt)
    
    # Генерируем ответ
    result = LLMResponse()
    try:
        # Используем синглтон - всегда получаем тот же экземпляр
        llm = LLMService()
        
        # Запускаем генерацию в отдельном потоке
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: llm.generate_response(data.promt)
        )
        print('*'*100)
        llm_text = response.text
        print('-'*100)
        result.time = response.time
        print('='*100)
    except Exception as e:
        result.text = f"Ошибка генерации: {str(e)}"
        llm_text = ""
    
    for part in data.template:
        if result.text != "":
            result.text += "\n"
        if "obligatury_text-" in part:
            result.text += data.obligatury_text[int(part.replace("obligatury_text-", ""))]
        elif part == "llm_text":
            result.text += llm_text
    
    return result
