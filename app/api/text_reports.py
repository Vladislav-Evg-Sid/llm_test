from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.text_reports import TableStandart, LLMResponse, LLMRequest
from app.db.connect_db import get_async_session
from app.services import table_rep_manager as tableRepManager
from app.services import llm_service as llmService


router = APIRouter(
    prefix="/textreports",
    tags=["textreports"]
)


# Запросы в БД !!!ТЕСТОВОЕ!!!
@router.post("/db/test/query/all")
async def test_querry(section_num: int, table_num: int, session: AsyncSession = Depends(get_async_session)) -> TableStandart:
    return await tableRepManager.get_table_by_section(session, section_num, table_num)

# Формирование первого раздела
@router.post("/report/generate/section")
async def generate_sections(request: LLMRequest, section_code: str = "1.7.", session: AsyncSession = Depends(get_async_session)) -> LLMResponse:
    return await llmService.get_generated_text_on_subject_by_section(session, request, section_code)
