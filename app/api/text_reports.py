from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io

from app.schemas.text_reports import TableStandart, LLMResponse, LLMRequest
from app.db.connect_db import get_async_session
from app.services.llm_service import table_rep_manager as tableRepManager
from app.services.llm_service import llm_service as llmService
from app.services.llm_service import get_file_by_data as getFileByData


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

@router.post("/file")
async def get_file(section_num: int, session: AsyncSession = Depends(get_async_session), background_tasks: BackgroundTasks = BackgroundTasks()):
    buffer = io.BytesIO()
    response_file = await getFileByData.get_docx_file(session, section_num)
    response_file.save(buffer)
    buffer.seek(0)
    background_tasks.add_task(cleanup_buffer, buffer)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=report.docx"}
    )

def cleanup_buffer(buffer: io.BytesIO):
    try:
        buffer.close()
    except Exception as e:
        print(f"Error cleaning buffer: {e}")